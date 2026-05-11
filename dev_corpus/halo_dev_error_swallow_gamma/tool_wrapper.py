def safe_execute(func, **kwargs):
    try:
        result = func(**kwargs)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
