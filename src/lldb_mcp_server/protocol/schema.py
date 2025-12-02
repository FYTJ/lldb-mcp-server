def make_response(req_id, result):
    return {"id": str(req_id), "result": result}

def make_error(req_id, code, message, data=None):
    payload = {"id": str(req_id), "error": {"code": int(code), "message": str(message)}}
    if data:
        payload["error"]["data"] = data
    return payload
