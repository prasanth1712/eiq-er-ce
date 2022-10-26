# -*- coding: utf-8 -*-
import logging

import requests
import sqlalchemy
from flask import current_app
from requests.auth import HTTPBasicAuth

from polylogyx.db.database import db
from polylogyx.db.models import Alerts, ResultLogScan, ThreatIntelCredentials

from .base import AbstractIntelPlugin

url = "https://api.xforce.ibmcloud.com:443"


class IBMxForceIntel(AbstractIntelPlugin):
    LEVEL_MAPPINGS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    def __init__(self, config):
        levelname = config.get("level", "debug")
        self.name = "ibmxforce"
        self.level = self.LEVEL_MAPPINGS.get(levelname, logging.DEBUG)
        self.api_keys_added = False

    def update_credentials(self):
        self.key = None
        self.api_pass = None
        credentials = (
            db.session.query(ThreatIntelCredentials).filter(ThreatIntelCredentials.intel_name == "ibmxforce").first()
        )
        if credentials and "key" in credentials.credentials and "pass" in credentials.credentials:
            self.key = credentials.credentials["key"]
            self.api_pass = credentials.credentials["pass"]
            self.api_keys_added = True
            current_app.logger.info("IBMxForce  api  configured")
        else:
            self.api_keys_added = False
            current_app.logger.warn("IBMxForce  api not configured")

    def analyse_hash(self, value, type, node):
        # TODO(andrew-d): better message?
        if self.api_keys_added == True:
            self.send_request(url + "/malware/", value, type)

    def analyse_pending_hashes(self):
        # TODO(andrew-d): better message?
        result_log_scans = (
            ResultLogScan.query.filter(sqlalchemy.not_(ResultLogScan.reputations.has_key(self.name)))
            .filter(ResultLogScan.scan_type.in_(["md5", "sha1", "sha256"]))
            .limit(4)
            .all()
        )
        if self.api_keys_added == True:
            for result_log_scan in result_log_scans:
                if self.send_request(url + "/malware/", result_log_scan, result_log_scan.scan_type) == 401:
                    break

    def analyse_domain(self, value, type, node):
        # TODO(andrew-d): better message?
        current_app.logger.log(self.level, "Triggered alert: ")

    def send_request(self, apiurl, result_log_scan_elem, type):
        value = result_log_scan_elem.scan_value
        fullurl = apiurl + value
        response_code = 0
        if self.name not in result_log_scan_elem.reputations:
            response = requests.get(
                fullurl,
                params="",
                auth=HTTPBasicAuth(self.key, self.api_pass),
                timeout=15,
            )
            response_code = response.status_code
            if response.status_code == 200:
                all_json = response.json()
                newReputations = dict(result_log_scan_elem.reputations)
                newReputations[self.name] = all_json
                risks = ["high", "medium"]
                if "malware" in all_json and "risk" in all_json["malware"] and all_json["malware"]["risk"] in risks:
                    newReputations[self.name + "_detected"] = True
                result_log_scan_elem.reputations = newReputations
                db.session.add(result_log_scan_elem)

                db.session.commit()
            elif response.status_code == 400 or response.status_code == 404:
                result_log_scan_elem.reputations[self.name] = {}
                db.session.add(result_log_scan_elem)
                db.session.commit()
            elif response.status_code == 401:
                return 401

        return response_code

    def generate_alerts(self):

        try:
            from polylogyx.db.database import db
            from polylogyx.db.models import ResultLogScan
            from polylogyx.utils.intel import check_and_save_intel_alert

            source = self.name

            result_log_scans = (
                db.session.query(ResultLogScan)
                .filter(ResultLogScan.reputations[source + "_detected"].astext.cast(sqlalchemy.Boolean).is_(True))
                .all()
            )
            for result_log_scan in result_log_scans:
                severity = Alerts.INFO
                if result_log_scan.reputations[source]["malware"]["risk"] == "high":
                    severity = Alerts.CRITICAL
                elif result_log_scan.reputations[source]["malware"]["risk"] == "medium":
                    severity = Alerts.MEDIUM

                check_and_save_intel_alert(
                    scan_id=result_log_scan.id,
                    scan_type=result_log_scan.scan_type,
                    scan_value=result_log_scan.scan_value,
                    data=result_log_scan.reputations[source],
                    source=source,
                    severity=severity,
                )
        except Exception as e:
            current_app.logger.error(e)
