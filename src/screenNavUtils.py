import json


def mapScreenNavValueToArgs(value: str):
    try:
        json_data = json.loads(value)  # Parse JSON
        route = json_data.get("route")
        args_raw = json_data.get("args")
        args = json.loads(args_raw) if args_raw else None
        pathUri = None
        withHaptic = None
        if args and isinstance(args, dict):
            mMap = args.get("mMap")
            if mMap:
                pathUri = mMap.get("pathUri")
                withHaptic = mMap.get("withHaptic")
        return {
            "route": route,
            "pathUri": pathUri,
            "withHaptic": withHaptic,
            "args": args,
        }
    except (json.JSONDecodeError, TypeError):
        return None
