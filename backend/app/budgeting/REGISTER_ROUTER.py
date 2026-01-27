"""
Add this to backend/app/main.py to register the budgeting router.

Find the section where other routers are registered and add:

    from app.budgeting.routes import router as budgeting_router

    # ... other router includes ...

    app.include_router(budgeting_router, prefix="/api/v1")

Example full registration block:

    # API Routes
    from app.auth.routes import router as auth_router
    from app.customers.routes import router as customers_router
    from app.budgeting.routes import router as budgeting_router

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(customers_router, prefix="/api/v1")
    app.include_router(budgeting_router, prefix="/api/v1")
"""
