class MailProvider:
    @staticmethod
    async def send(notification, attempt_number):
        metadata = notification.get("metadata") or {}
        flow = metadata.get("mock_flow", ["success"])

        index = min(attempt_number - 1, len(flow) - 1)
        action = flow[index]

        if action == "success":
            return {"ok": True, "attempt": attempt_number}

        if action == "temp_fail":
            raise Exception(f"TEMP_FAIL {attempt_number}")

        if action == "perm_fail":
            raise Exception(f"PERM_FAIL {attempt_number}")

        raise Exception(f"UNKNOWN_ACTION {attempt_number}")

    @staticmethod
    def can_retry(error, notification):
        error_str = str(error).lower()

        # Permanent failure
        if "invalid" in error_str:
            return False

        # Max attempts reached
        if notification["attempt_count"] >= notification["max_attempts"]:
            return False

        return True
