from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Body, Query
from pydantic import BaseModel
import cloudinary
import cloudinary.uploader

from py_nyc.web.core.config import Settings, get_settings
from py_nyc.web.utils.auth import TokenData, get_user_info

cloudinary_router = APIRouter(prefix="/cloudinary")


class DeleteImagesRequest(BaseModel):
    public_ids: List[str]


async def _upload_images_internal(
    files: List[UploadFile],
    settings: Settings,
    user_id: str,
    listing_id: Optional[str] = None
) -> dict:
    """
    Internal helper function to upload images to Cloudinary.
    Can be called from other routers without HTTP dependency injection.
    """
    # Configure Cloudinary with settings
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
    )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )

    if len(files) > 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 8 files allowed"
        )

    # Build folder path: /{env}/{user_id}/{listing_id}
    folder_path = f"{settings.cloudinary_env}/{user_id}"
    if listing_id:
        folder_path = f"{folder_path}/{listing_id}"

    uploaded_images = []

    for file in files:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file.filename} is not a valid image"
            )

        try:
            # Read file content
            file_content = await file.read()

            # Upload to Cloudinary with structured folder path
            upload_result = cloudinary.uploader.upload(
                file_content,
                resource_type="auto",
                folder=folder_path,
                use_filename=True,
                unique_filename=True
            )

            # Format response to match frontend expectations
            image_data = {
                "name": upload_result.get("original_filename", file.filename),
                "src": upload_result["secure_url"],
                "cld_public_id": upload_result["public_id"],
                "file_size": upload_result["bytes"],
                "file_type": upload_result["format"]
            }

            uploaded_images.append(image_data)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload {file.filename}: {str(e)}"
            )

    return {"images": uploaded_images}


@cloudinary_router.post("/upload")
async def upload_images(
    files: List[UploadFile] = File(...),
    listing_id: Optional[str] = Query(None, description="Listing ID for organizing uploads"),
    settings: Annotated[Settings, Depends(get_settings)] = None,
    user: Annotated[TokenData, Depends(get_user_info)] = None
):
    """
    Upload multiple images to Cloudinary through backend to keep API keys secure.
    Images are organized by: /{environment}/{user_id}/{listing_id}/
    If listing_id is not provided, images are uploaded to: /{environment}/{user_id}/
    """
    return await _upload_images_internal(files, settings, user.id, listing_id)


@cloudinary_router.delete("/delete/{public_id:path}")
async def delete_image(
    public_id: str,
    settings: Annotated[Settings, Depends(get_settings)] = None
):
    """
    Delete an image from Cloudinary
    """
    # Configure Cloudinary with settings
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
    )

    try:
        result = cloudinary.uploader.destroy(public_id)

        if result.get("result") == "ok":
            return {"success": True, "message": "Image deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete image"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete image: {str(e)}"
        )


async def _delete_images_internal(public_ids: list[str], settings: Settings) -> dict:
    """
    Internal helper function to delete images from Cloudinary.
    Can be called from other routers without HTTP dependency injection.
    """
    # Configure Cloudinary with settings
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
    )

    if not public_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No public IDs provided"
        )

    if len(public_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 images can be deleted at once"
        )

    deleted_images = []
    failed_deletions = []

    for public_id in public_ids:
        try:
            result = cloudinary.uploader.destroy(public_id)

            if result.get("result") == "ok":
                deleted_images.append({
                    "public_id": public_id,
                    "status": "deleted",
                    "message": "Successfully deleted"
                })
            else:
                failed_deletions.append({
                    "public_id": public_id,
                    "status": "failed",
                    "message": "Failed to delete from Cloudinary"
                })
        except Exception as e:
            failed_deletions.append({
                "public_id": public_id,
                "status": "error",
                "message": str(e)
            })

    return {
        "success": len(failed_deletions) == 0,
        "deleted_count": len(deleted_images),
        "failed_count": len(failed_deletions),
        "deleted_images": deleted_images,
        "failed_deletions": failed_deletions
    }


@cloudinary_router.post("/delete")
async def delete_images(
    delete_request: DeleteImagesRequest = Body(...),
    settings: Annotated[Settings, Depends(get_settings)] = None
):
    """
    Delete multiple images from Cloudinary via HTTP endpoint.
    """
    return await _delete_images_internal(delete_request.public_ids, settings)
