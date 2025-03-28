from passlib.context import CryptContext

pwd_cxt = CryptContext(schemes =["bcrypt"],deprecated="auto")

def bcrypt_pwd(password:str):
      return pwd_cxt.hash(password)
   
def verify_pwd(hashed, normal):
      return pwd_cxt.verify(normal, hashed)