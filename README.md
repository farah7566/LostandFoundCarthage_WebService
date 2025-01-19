# Lost and Found API

This is a Flask-based RESTful API that allows users to report and retrieve lost items. It features JWT authentication, image uploads, and supports two categories of users: travelers and agents. The API provides endpoints for reporting, listing, and updating lost items.

## Features
- **Report Lost Items**: Travelers can report lost items along with details and an optional image.
- **Retrieve Lost Items**: Users can fetch details of lost items, either by item ID or by listing all items.
- **Update Lost Item Status**: Authorized users (agents or admin) can update the status of reported lost items (e.g., "Found", "Claimed").
- **JWT Authentication**: Secure routes are protected using JSON Web Token (JWT).

## Installation

### Prerequisites
- Python 3.8+
- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Other dependencies listed in `requirements.txt`

### Steps to run the project locally

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/lost-and-found-api.git
   cd lost-and-found-api
