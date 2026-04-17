from common.mcp_base import error_envelope, ok_envelope, ErrorCode


def test_ok_envelope_wraps_data():
    env = ok_envelope({"a": 1})
    assert env == {"ok": True, "data": {"a": 1}}


def test_error_envelope_shape():
    env = error_envelope(ErrorCode.BAD_INPUT, "bad x", detail={"x": 1})
    assert env == {
        "ok": False,
        "error": {"code": "BAD_INPUT", "message": "bad x", "detail": {"x": 1}},
    }


def test_error_envelope_no_detail_defaults_to_empty_dict():
    env = error_envelope(ErrorCode.TIMEOUT, "slow")
    assert env["error"]["detail"] == {}
