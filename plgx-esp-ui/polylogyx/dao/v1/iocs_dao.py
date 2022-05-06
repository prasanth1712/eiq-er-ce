from polylogyx.models import IOCIntel


def del_manual_threat_intel(intel_type):
    return IOCIntel.query.filter(IOCIntel.intel_type == intel_type).delete()


def create_manual_threat_intel(intel_type, type, value, severity, threat_name):
    return IOCIntel.create(intel_type=intel_type, type=type, value=value, severity=severity, threat_name=threat_name)


def get_intel_data(intel_type):
    return IOCIntel.query.filter(IOCIntel.intel_type == intel_type).all()
