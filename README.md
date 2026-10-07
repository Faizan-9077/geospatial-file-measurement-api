\# Geospatial File Measurement API



A FastAPI backend for processing geospatial files and calculating feature measurements.



The API accepts \*\*KML files\*\* and \*\*ZIP archives containing Shapefiles\*\*, extracts feature information, handles coordinate reference systems (CRS), and calculates:



\- Polygon / MultiPolygon → area

\- LineString / MultiLineString → length

\- Point → no measurement

\- Unsupported geometry → handled without crashing



\---



\## Features



\- Upload `.kml` files

\- Upload `.zip` files containing Shapefiles

\- Extract feature geometry and attributes

\- Preserve the original CRS

\- Automatically select a suitable projected CRS for measurements

\- Calculate area in square meters

\- Calculate length in meters

\- Persist processed file metadata and measurements

\- Secure ZIP extraction with path-traversal protection

\- Validate Shapefile components

\- Reject ambiguous ZIP archives containing multiple Shapefiles

\- REST APIs for upload, file retrieval, and measurements

\- Automated test suite with 18 tests



\---



\## Tech Stack



\### Backend



\- Python

\- FastAPI

\- Uvicorn



\### Geospatial



\- GeoPandas

\- Shapely

\- PyProj

\- Fiona



\### Data / Storage



\- JSON file-based persistence

\- PostgreSQL is not required for this assignment



\### Testing



\- Pytest

\- FastAPI TestClient



\---



\## Project Structure



```text

geospatial-file-measurement-api/

│

├── app/

│   ├── \_\_init\_\_.py

│   ├── main.py

│   │

│   ├── api/

│   │   ├── \_\_init\_\_.py

│   │   └── routes/

│   │       ├── \_\_init\_\_.py

│   │       └── files.py

│   │

│   └── services/

│       ├── \_\_init\_\_.py

│       ├── file\_processor.py

│       ├── crs.py

│       ├── measurement.py

│       ├── storage.py

│       └── serialization.py

│

├── data/

│   └── files.json

│

├── sample\_data/

│   └── test.kml

│

├── tests/

│   ├── test\_api.py

│   ├── test\_file\_processor.py

│   └── test\_measurement.py

│

├── uploads/

│   └── .gitkeep

│

├── .gitignore

├── pytest.ini

├── requirements.txt

└── README.md

```



\---



\## Architecture



The application separates API handling from geospatial processing.



```text

Client

&#x20; │

&#x20; │ POST /api/files/

&#x20; ▼

FastAPI Route

&#x20; │

&#x20; ▼

File Processor

&#x20; │

&#x20; ├── KML ────────────────┐

&#x20; │                        │

&#x20; └── ZIP                  │

&#x20;      │                   │

&#x20;      ├── Safe extraction │

&#x20;      ├── Find .shp       │

&#x20;      ├── Validate files  │

&#x20;      └── Read Shapefile  │

&#x20;                          ▼

&#x20;                   GeoDataFrame

&#x20;                          │

&#x20;                          ▼

&#x20;                   CRS Detection

&#x20;                          │

&#x20;                          ▼

&#x20;                 Projected CRS

&#x20;                          │

&#x20;                          ▼

&#x20;                 Measurement Engine

&#x20;                          │

&#x20;                          ▼

&#x20;                 JSON Serialization

&#x20;                          │

&#x20;                          ▼

&#x20;                    JSON Storage

```



The main responsibilities are separated into services:



\- `file\_processor.py` — reads KML and safely processes ZIP/Shapefile uploads.

\- `crs.py` — determines the CRS suitable for measurement.

\- `measurement.py` — calculates feature measurements.

\- `serialization.py` — converts values into JSON-safe representations.

\- `storage.py` — persists processed file records.

\- `files.py` — exposes the REST API endpoints.



\---



\## File Processing Flow



\### KML



For a KML upload:



```text

KML upload

&#x20;  ↓

GeoPandas reads KML

&#x20;  ↓

GeoDataFrame

&#x20;  ↓

CRS detection

&#x20;  ↓

Measurement

```



\### ZIP / Shapefile



ZIP processing follows a stricter flow:



```text

ZIP upload

&#x20;  ↓

Validate ZIP member paths

&#x20;  ↓

Temporary extraction directory

&#x20;  ↓

Find .shp

&#x20;  ↓

Ensure exactly one Shapefile exists

&#x20;  ↓

Validate .shp / .shx / .dbf / .prj

&#x20;  ↓

GeoPandas reads .shp

&#x20;  ↓

CRS detection

&#x20;  ↓

Measurement

```



The extracted files are stored only in a temporary directory and are automatically removed after processing.



\---



\## ZIP Security



ZIP archives are not extracted blindly.



Each archive member is checked before extraction. Absolute paths and paths containing `..` are rejected to prevent path traversal attacks.



For example, an archive containing:



```text

../../evil.txt

```



is rejected.



The API returns an error such as:



```json

{

&#x20; "detail": "Unable to process geospatial file: Unsafe path detected in ZIP archive: ../evil.txt"

}

```



\### Shapefile Validation



A valid Shapefile normally consists of multiple related files.



This implementation validates:



```text

.shp

.shx

.dbf

.prj

```



The `.prj` file is required because the CRS is needed for reliable measurement calculations.



The API also rejects ZIP archives containing multiple `.shp` files rather than arbitrarily selecting one.



\---



\## CRS Handling



Geospatial coordinates can be represented in geographic CRS such as:



```text

EPSG:4326

```



EPSG:4326 represents longitude and latitude in degrees.



Area and length should not be calculated directly from geographic degree coordinates because degrees are angular units rather than linear measurement units.



The API therefore follows this logic:



```text

Input GeoDataFrame

&#x20;      │

&#x20;      ├── Projected CRS?

&#x20;      │       │

&#x20;      │       └── Yes → use existing CRS

&#x20;      │

&#x20;      └── Geographic CRS

&#x20;              │

&#x20;              ▼

&#x20;       Estimate suitable UTM CRS

&#x20;              │

&#x20;              ▼

&#x20;       Transform geometries

&#x20;              │

&#x20;              ▼

&#x20;       Calculate measurements

```



For example, the sample data around Bangalore uses:



```text

Source CRS:

EPSG:4326



Measurement CRS:

EPSG:32643

```



Measurements are therefore returned in metric units.



\---



\## Measurement Logic



\### Polygon / MultiPolygon



Area is calculated after transforming the geometry into the measurement CRS.



```text

unit: square\_meters

```



\### LineString / MultiLineString



Length is calculated after CRS transformation.



```text

unit: meters

```



\### Point



Points do not have an area or length measurement.



```json

{

&#x20; "measurement": null,

&#x20; "unit": null

}

```



\### Unsupported Geometry



Unsupported geometry types are returned without a measurement rather than causing the complete request to fail.



\---



\## API Endpoints



Base URL:



```text

http://127.0.0.1:8000

```



Interactive API documentation:



```text

http://127.0.0.1:8000/docs

```



\---



\### 1. Upload a File



```http

POST /api/files/

```



Accepts:



\- `.kml`

\- `.zip` containing a Shapefile



Example using `curl`:



```bash

curl -X POST "http://127.0.0.1:8000/api/files/" \\

&#x20; -H "accept: application/json" \\

&#x20; -H "Content-Type: multipart/form-data" \\

&#x20; -F "file=@sample\_data/test.kml"

```



Example response:



```json

{

&#x20; "id": "14edff87-30e5-423c-ae5e-cd673ad2f386",

&#x20; "filename": "test.kml",

&#x20; "feature\_count": 3,

&#x20; "crs": "EPSG:4326",

&#x20; "measurement\_crs": "EPSG:32643",

&#x20; "geometry\_types": \[

&#x20;   "Point",

&#x20;   "LineString",

&#x20;   "Polygon"

&#x20; ],

&#x20; "status": "COMPLETED",

&#x20; "measurements": \[]

}

```



The exact generated ID and measurement values depend on the uploaded file.



\---



\### 2. Get File Information



```http

GET /api/files/{id}

```



Example:



```bash

curl "http://127.0.0.1:8000/api/files/<file\_id>"

```



Returns the stored metadata and calculated measurements for the file.



\---



\### 3. Get Measurements



```http

GET /api/files/{id}/measurements

```



Example:



```bash

curl "http://127.0.0.1:8000/api/files/<file\_id>/measurements"

```



Example response structure:



```json

{

&#x20; "file\_id": "bad2b874-6900-45da-8e0a-2fe0d45b9436",

&#x20; "filename": "test\_shapefile.zip",

&#x20; "measurement\_crs": "EPSG:32643",

&#x20; "feature\_count": 2,

&#x20; "measurements": \[

&#x20;   {

&#x20;     "feature\_id": 0,

&#x20;     "geometry\_type": "Polygon",

&#x20;     "geometry": {},

&#x20;     "crs": "EPSG:4326",

&#x20;     "properties": {

&#x20;       "name": "Test Polygon 1",

&#x20;       "category": "polygon"

&#x20;     },

&#x20;     "measurement": 1201683.9190970361,

&#x20;     "unit": "square\_meters"

&#x20;   }

&#x20; ]

}

```



\---



\## Setup



\### 1. Clone the repository



```bash

git clone https://github.com/Faizan-9077/geospatial-file-measurement-api.git

cd geospatial-file-measurement-api

```



\### 2. Create a virtual environment



Windows PowerShell:



```powershell

python -m venv venv

```



Activate it:



```powershell

venv\\Scripts\\activate

```



\### 3. Install dependencies



```powershell

pip install -r requirements.txt

```



\### 4. Start the server



```powershell

uvicorn app.main:app --reload

```



The API will be available at:



```text

http://127.0.0.1:8000

```



Swagger documentation:



```text

http://127.0.0.1:8000/docs

```



\---



\## Testing



The project uses Pytest for automated testing.



Run the complete test suite:



```powershell

pytest -v

```



Current test coverage includes:



\### API Tests



\- Root endpoint

\- KML upload

\- ZIP/Shapefile upload

\- File retrieval

\- Measurement retrieval

\- Missing file handling



\### File Processing Tests



\- Valid Shapefile ZIP

\- ZIP without `.shp`

\- Missing Shapefile component

\- Multiple Shapefiles

\- ZIP path traversal protection



\### CRS / Measurement Tests



\- Polygon area

\- MultiPolygon area

\- LineString length

\- MultiLineString length

\- Point without measurement

\- Projected CRS handling

\- Missing CRS handling



Current result:



```text

18 passed

```



\---



\## Error Handling



The API distinguishes between invalid input and unexpected server failures.



\### Client / Input Errors



Invalid geospatial input results in:



```text

HTTP 400 Bad Request

```



Examples include:



\- Unsupported file format

\- Invalid ZIP structure

\- Missing Shapefile

\- Missing required Shapefile components

\- Multiple Shapefiles

\- Unsafe ZIP paths

\- Missing CRS



\### Unexpected Errors



Unexpected application failures return:



```text

HTTP 500 Internal Server Error

```



with a generic message rather than exposing internal implementation details.



\---



\## Data Storage



For this assignment, processed file metadata is stored in:



```text

data/files.json

```



The storage layer is intentionally simple and file-based.



Uploaded source files are temporarily stored while being processed and are removed afterward.



This keeps the implementation lightweight and avoids introducing unnecessary database infrastructure for the assignment.



\---



\## Design Decisions



\### 1. FastAPI



FastAPI provides a lightweight API framework with automatic OpenAPI/Swagger documentation and straightforward file-upload handling.



\### 2. GeoPandas



GeoPandas provides the main abstraction for reading geospatial files and working with geometries and CRS information.



\### 3. Temporary ZIP Extraction



ZIP contents are extracted into a temporary directory rather than permanently storing extracted Shapefile components.



\### 4. Reject Ambiguous ZIPs



A ZIP containing multiple Shapefiles is rejected instead of selecting one arbitrarily.



This makes the API behavior deterministic.



\### 5. Require `.prj`



The `.prj` file is required because measurement calculations depend on knowing the coordinate reference system.



\### 6. Projected CRS for Measurements



Geographic coordinates are transformed into a suitable projected CRS before calculating area or length.



This avoids returning measurements in meaningless degree-based units.



\### 7. JSON Persistence



A simple JSON storage layer was selected because the assignment does not require a database and the main focus is geospatial file processing.



\---



\## Learning



Through this project, the main areas explored were:



\- FastAPI file upload APIs

\- GeoPandas and Shapely

\- Shapefile structure

\- Coordinate Reference Systems

\- Geographic vs projected CRS

\- UTM-based measurement

\- Safe ZIP extraction

\- Path traversal protection

\- Temporary file handling

\- JSON serialization of geospatial data

\- REST API design

\- Automated testing with Pytest

\- API testing with FastAPI TestClient



\---



\## Future Scope



Possible improvements for a production system include:



\- PostgreSQL/PostGIS for persistent geospatial storage

\- Asynchronous/background processing for large files

\- File-size and resource limits

\- More geospatial formats such as GeoJSON and GeoPackage

\- Support for selecting a measurement CRS explicitly

\- More advanced geometry validation and repair

\- Authentication and authorization

\- Object storage such as Amazon S3

\- Structured logging and monitoring

\- Pagination for very large feature collections

\- More detailed API schemas and validation

\- Containerization with Docker



\---



\## Project Status



The current implementation supports the required assignment workflow:



```text

KML / ZIP Shapefile

&#x20;       ↓

Secure File Processing

&#x20;       ↓

Feature Extraction

&#x20;       ↓

CRS Detection

&#x20;       ↓

Projected CRS Transformation

&#x20;       ↓

Area / Length Measurement

&#x20;       ↓

Persistence

&#x20;       ↓

REST API

```



Automated test status:



```text

18 tests passed

```

