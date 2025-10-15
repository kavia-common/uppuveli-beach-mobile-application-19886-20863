from app.main import app as application  # import under a different name

# PUBLIC_INTERFACE
app = application  # re-export app for ASGI servers and to satisfy linter usage
