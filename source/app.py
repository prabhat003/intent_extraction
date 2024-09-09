import os
import sys
import json
import time
import asyncio
import uvicorn
import logging
import re
import ast
import cohere
# import streamlit as st
from logger import logger
from main import GetConfig, Generate
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from ast import literal_eval as le
from passlib.context import CryptContext
from werkzeug.exceptions import BadRequest
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm



sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import SessionLocal, engine, User, create_database

# Load variables from .env file
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')  # Provide a fallback secret key for demonstration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_IN_HOURS = os.getenv('ACCESS_TOKEN_EXPIRE_IN_HOURS')  # Provide a fallback expiry time


# Password context for hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

# Add CORS middleware if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as necessary
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    access_token: str
    token_type: str
    expires_in: str

class TokenData(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    username: Optional[str] = None

class QuestionRequest1(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    position_name: str
    company_name:str
    division_name: str
    seniority_level: str
    exp_in_years: str
    contract_type: str
    location: str
    work_arrangement: str

class QuestionRequest2(BaseModel):

    """_summary_

    Args:
        BaseModel (_type_): _description_
    """

    query: str

class LoginRequest(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    username: str
    password: str

class RegisterRequest(BaseModel):

    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    
    username: str
    password: str

def get_password_hash(password):

    """_summary_

    Args:
        password (_type_): _description_

    Returns:
        _type_: _description_
    """
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):

    """_summary_

    Args:
        plain_password (_type_): _description_
        hashed_password (bool): _description_

    Returns:
        _type_: _description_
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db, username: str):

    """_summary_

    Args:
        db (_type_): _description_
        username (str): _description_

    Returns:
        _type_: _description_
    """

    return db.query(User).filter(User.username == username).first()

def authenticate_user(db, username: str, password: str):

    """_summary_

    Args:
        db (_type_): _description_
        username (str): _description_
        password (str): _description_

    Returns:
        _type_: _description_
    """

    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):

    """
    Args:
        data (dict): _description_
        expires_delta (Optional[timedelta], optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})

    # else:
    #     expire = datetime.now(timezone.utc) + timedelta(hours=3)

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_project_dir():
    """_summary_

    Returns:
        _type_: _description_
    """
    try:
        # This works when running as a script
        current_script_path = Path(__file__).resolve()
        current_script_dir = current_script_path.parent
    except NameError:
        # This works when running interactively
        current_script_dir = Path.cwd()
    
    return current_script_dir


async def get_current_user(token: str = Depends(oauth2_scheme)):

    """_summary_

    Args:
        token (str, optional): _description_. Defaults to Depends(oauth2_scheme).

    Raises:
        credentials_exception: _description_
        credentials_exception: _description_
        credentials_exception: _description_

    Returns:
        _type_: _description_
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials, Make sure your bearer token has not expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        expiry_time = payload.get("exp")
        if expiry_time is None:
            token_data = TokenData(username=username)

        else:
            if (datetime.now(timezone.utc) > datetime.fromtimestamp(expiry_time, tz=timezone.utc)):
                raise credentials_exception
        
        token_data = TokenData(username=username)

    except JWTError:
            raise credentials_exception
    
    db = SessionLocal()
    user = get_user(db, token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Exception handler for validation errors
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.method == "POST":
        start_time = time.time()  # Record the start time
        try:
            # Read the request body
            request_body = await request.json()
            response = await call_next(request)

            # Calculate the response time
            response_time = time.time() - start_time

            # Log request details and response status code
            logger.info(f'Endpoint: {request.url.path}, Body: {request_body}, Headers: {dict(request.headers)}, Status: {response.status_code}, Response Time: {response_time:.4f} seconds')

        except Exception as e:
            
            response_time = time.time() - start_time
            logger.error(f"Failed to read request body: {e}, Response Time: {response_time:.4f} seconds")
            return await call_next(request)
    else:
        response = await call_next(request)
    return response


async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, func, *args)
        executor.shutdown(wait=True)  # Ensure all threads are completed and resources are cleaned up
        return result

def remove_surrounding_quotes(s: str) -> str:

    """_summary_

    Args:
        s (str): _description_

    Returns:
        str: _description_
    """
    # Check if the string starts and ends with the same type of quote
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s

def extract_between_curly_braces(input_str):
    """_summary_

    Args:
        input_str (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Define a regular expression pattern to match text between curly braces
    pattern = r'\{([^{}]*)\}'

    # Use re.findall() to find all matches of the pattern in the input string
    matches = re.findall(pattern, input_str)

    # Join the matches into a single string separated by commas
    result = ', '.join(matches)

    return '{'+result+'}'


def get_results(query):

    try:
        vars = GetConfig()
        COHERE_API_KEY = vars.COHERE_API_KEY
        question = remove_surrounding_quotes(query.query)
        prompt_generator = Generate(str(question))
        final_prompt = prompt_generator.get_prompt()

        co = cohere.Client(api_key = COHERE_API_KEY)

        response = co.generate(
            model = "command",
            prompt=final_prompt,
            seed=32
        )

        clean_json_string = extract_between_curly_braces(response.generations[0].text)

        logger.info(f'Result generated...')

        return str(clean_json_string)

    except Exception as e:
        logger.info("Error occured in ambiguity check => "+str(e))


@app.post("/register")
async def register_user(data: RegisterRequest):
    db = SessionLocal()
    try:
        user = get_user(db, data.username)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists, try with a different username",
            )

        hashed_password = get_password_hash(data.password)
        new_user = User(username=data.username, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"status": "User registered successfully"}
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    
    finally:
        db.close()

@app.post("/token", response_model=Token)
async def login_for_access_token(data: LoginRequest):
    with SessionLocal() as db:
        user = authenticate_user(db, data.username, data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        vars = GetConfig()
        ACCESS_TOKEN_EXPIRE_IN_HOURS = vars.ACCESS_TOKEN_EXPIRE_IN_HOURS

        # Handle token expiration
        if ACCESS_TOKEN_EXPIRE_IN_HOURS == "None":
            access_token = create_access_token(data={"sub": user.username})
            return {"access_token": access_token, "token_type": "bearer", "expires_in": "immortal"}
        else:
            access_token_expires = timedelta(hours=int(ACCESS_TOKEN_EXPIRE_IN_HOURS))
            access_token = create_access_token(
                data={"sub": user.username}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer", "expires_in": f"{ACCESS_TOKEN_EXPIRE_IN_HOURS} hours"}
   
@app.post("/extract")
async def generate_question(data: QuestionRequest2, current_user: dict = Depends(get_current_user)):

    """_summary_

    Raises:
        HTTPException: _description_
        HTTPException: _description_

    Returns:
        _type_: _description_
    """

    try:

        # Run functions in parallel
        # response = await run_in_executor(get_results, data)
        response = get_results(data)
        formatted_response = ast.literal_eval(str(response))
        return {
                "query": data.query,
                "answer": formatted_response,
        }
    except BadRequest:
        raise HTTPException(status_code=400, detail="Invalid request data")
    
    except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail=e.errors()
            )

    except Exception as e:
        logger.exception(e)

@app.get("/health")
async def health_check():
    
    """_summary_

    Returns:
        _type_: _description_
    """

    return {"status": "I am alive, thanks for checking"}

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5001)