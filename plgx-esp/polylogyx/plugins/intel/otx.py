# -*- coding: utf-8 -*-

import logging

import sqlalchemy
from flask import current_app
from OTXv2 import OTXv2

from polylogyx.db.database import db
from polylogyx.db.models import ResultLogScan, ThreatIntelCredentials
from polylogyx.utils.intel import check_and_save_intel_alert
from polylogyx.utils.otx.is_malicious import *

from .base import AbstractIntelPlugin


class OTXIntel(AbstractIntelPlugin):
    LEVEL_MAPPINGS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    def __init__(self, config):
        self.name = "alienvault"
        levelname = config.get("level", "debug")
        self.otx = None

    def update_credentials(self):
        try:
            credentials = (
                db.session.query(ThreatIntelCredentials)
                .filter(ThreatIntelCredentials.intel_name == "alienvault")
                .first()
            )
            if credentials and "key" in credentials.credentials:
                self.otx = OTXv2(credentials.credentials["key"])
                current_app.logger.info("AlienVault OTX  api  configured")
                return True
            else:
                self.otx = None
                current_app.logger.warn("AlienVault OTX  api not configured")
        except Exception as e:
            current_app.logger.error(e)
        return False

    def analyse_hash(self, value, type, node):
        if self.otx:
            result_log_scan_elem = db.session.query(ResultLogScan).filter(ResultLogScan.scan_value == value).first()
            response = {}
            if result_log_scan_elem:
                if self.name not in result_log_scan_elem.reputations:
                    response = is_hash_malicious(value, self.otx)
                    newReputations = dict(result_log_scan_elem.reputations)
                    newReputations[self.name] = response
                    result_log_scan_elem.reputations = newReputations
                    db.session.add(result_log_scan_elem)
                    db.session.commit()
                else:
                    response = result_log_scan_elem.reputations[self.name]
            if "alerts" in response and len(response["alerts"]) > 0:
                check_and_save_intel_alert(
                    scan_type=type,
                    scan_value=value,
                    data=response["result"],
                    source=self.name,
                    severity="LOW",
                )

    def analyse_pending_hashes(self):
        if self.otx:
            result_log_scans = (
                ResultLogScan.query.filter(sqlalchemy.not_(ResultLogScan.reputations.has_key(self.name)))
                .filter(ResultLogScan.scan_type.in_(["md5", "sha1", "sha256"]))
                .limit(4)
                .all()
            )
            for result_log_scan_elem in result_log_scans:
                try:
                    response = is_hash_malicious(result_log_scan_elem.scan_value, self.otx)
                    newReputations = dict(result_log_scan_elem.reputations)
                    newReputations[self.name] = response
                    if "alerts" in response and len(response["alerts"]) > 0:
                        newReputations[self.name + "_detected"] = True
                    else:
                        newReputations[self.name + "_detected"] = False
                    result_log_scan_elem.reputations = newReputations
                    db.session.add(result_log_scan_elem)
                except Exception as e:
                    newReputations = dict(result_log_scan_elem.reputations)
                    newReputations[self.name] = {}
                    result_log_scan_elem.reputations = newReputations
                    db.session.add(result_log_scan_elem)
                    current_app.logger.error(e)
            db.session.commit()

    def generate_alerts(self):
        try:
            source = self.name
            from polylogyx.db.database import db
            from polylogyx.db.models import ResultLogScan
            from polylogyx.utils.intel import check_and_save_intel_alert

            result_log_scans = (
                db.session.query(ResultLogScan)
                .filter(ResultLogScan.reputations[source + "_detected"].astext.cast(sqlalchemy.Boolean).is_(True))
                .all()
            )
            for result_log_scan in result_log_scans:
                check_and_save_intel_alert(
                    scan_id=result_log_scan.id,
                    scan_type=result_log_scan.scan_type,
                    scan_value=result_log_scan.scan_value,
                    data=result_log_scan.reputations[source],
                    source=source,
                    severity="LOW",
                )

        except Exception as e:
            current_app.logger.error(e)

    def analyse_domain(self, value, type, node):
        # TODO(andrew-d): better message?

        current_app.logger.log(self.level, "Triggered alert: ")
