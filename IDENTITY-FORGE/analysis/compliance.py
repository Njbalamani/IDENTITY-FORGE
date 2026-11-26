CONTROL_MAP = {
    "EXCESSIVE_PRIVILEGE": {
        "nist_csf": ["PR.AA-05", "PR.AA-07"],
        "cis_controls": ["5.4", "6.5"],
        "zero_trust_principles": ["Least privilege", "Explicit verification"],
    },
    "CONFLICTING_ROLE": {
        "nist_csf": ["PR.AA-05", "ID.RA-01"],
        "cis_controls": ["5.4", "6.8"],
        "zero_trust_principles": ["Least privilege", "Assume breach"],
    },
    "INACTIVE_ACCESS": {
        "nist_csf": ["PR.AA-06", "PR.AA-07"],
        "cis_controls": ["5.4", "6.2"],
        "zero_trust_principles": ["Explicit verification", "Least privilege"],
    },
    "HIGH_RISK_PERMISSION": {
        "nist_csf": ["PR.AA-05", "PR.AA-06"],
        "cis_controls": ["6.5"],
        "zero_trust_principles": ["Least privilege"],
    },
    "ESCALATION_PATH": {
        "nist_csf": ["PR.AA-05", "DE.CM-01"],
        "cis_controls": ["6.8", "8.11"],
        "zero_trust_principles": ["Least privilege", "Continuous monitoring"],
    },
    "ANOMALY_DETECTION": {
        "nist_csf": ["DE.CM-01", "DE.CM-07", "ID.RA-07"],
        "cis_controls": ["8.11"],
        "zero_trust_principles": ["Continuous monitoring", "Assume breach"],
    },
    "ZERO_TRUST": {
        "nist_csf": ["PR.AA-03", "PR.AA-05", "PR.AA-07"],
        "cis_controls": ["5.4", "6.5"],
        "zero_trust_principles": ["Explicit verification", "Least privilege"],
    },
}

DEFAULT_CONTROLS = {
    "nist_csf": ["ID.RA-01"],
    "cis_controls": [],
    "zero_trust_principles": ["Continuous monitoring"],
}


def control_mapping(category):
    return CONTROL_MAP.get(category, DEFAULT_CONTROLS)
