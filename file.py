import io
import os
import secrets

import requests
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from pypdf import PdfReader, PdfWriter

app = FastAPI()

SHARED_SECRET = os.environ["PYTHON_SHARED_SECRET"]


class Document(BaseModel):
    record_id: int
    title: str
    url: str


class PackageRequest(BaseModel):
    bom_record_id: int
    package_name: str
    documents: list[Document]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-package")
def generate_package(
    request: PackageRequest,
    x_api_key: str | None = Header(default=None),
):
    if not x_api_key or not secrets.compare_digest(x_api_key, SHARED_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not request.documents:
        raise HTTPException(status_code=400, detail="No PDF documents received")

    writer = PdfWriter()

    for document in request.documents:
        response = requests.get(document.url, timeout=120)
        response.raise_for_status()

        reader = PdfReader(io.BytesIO(response.content))
        start_page = len(writer.pages)

        for page in reader.pages:
            writer.add_page(page)

        writer.add_outline_item(document.title, start_page)

    # This starter service merges PDFs but does not yet publish the output.
    # Add cloud storage, such as S3, then return its temporary download URL.
    raise HTTPException(
        status_code=501,
        detail="PDF merge works; configure cloud storage before production use."
    )
