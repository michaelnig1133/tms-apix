# Transport Management System API

A Django REST Framework API for managing transport requests with multi-level approval workflow.

## Quick Start

1. Set up environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Run the server:
   ```bash
   python manage.py runserver
   ```

## Testing

Run tests:
```bash
python manage.py test
```

Run specific test file:
```bash
python manage.py test core.tests.test_transport_workflow
```

## Main Features

- Transport request creation and approval workflow
- Vehicle management
- Role-based access control (Employee, Manager, CEO, etc.)
- JWT authentication