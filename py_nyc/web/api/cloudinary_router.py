import os
from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile, status, Body
from pydantic import BaseModel
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),

)

cloudinary_router = APIRouter(prefix="/cloudinary")


class DeleteImagesRequest(BaseModel):
    public_ids: List[str]


@cloudinary_router.post("/upload")
async def upload_images(files: List[UploadFile] = File(...)):
    """
    Upload multiple images to Cloudinary through backend to keep API keys secure
    """
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

            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_content,
                resource_type="auto",
                # folder="listings",  # Optional: organize uploads in folders
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


@cloudinary_router.delete("/delete/{public_id:path}")
async def delete_image(public_id: str):
    """
    Delete an image from Cloudinary
    """
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


@cloudinary_router.post("/delete")
async def delete_images(delete_request: DeleteImagesRequest = Body(...)):
    """
    Delete multiple images from Cloudinary
    """
    if not delete_request.public_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No public IDs provided"
        )

    if len(delete_request.public_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 images can be deleted at once"
        )

    deleted_images = []
    failed_deletions = []

    for public_id in delete_request.public_ids:
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
