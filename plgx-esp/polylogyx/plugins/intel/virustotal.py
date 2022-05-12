# -*- coding: utf-8 -*-
import logging

import requests
import sqlalchemy
import datetime as dt
from flask import current_app
from virus_total_apis import PublicApi as VirusTotalPublicApi

from polylogyx.db.database import db
from polylogyx.db.models import ResultLogScan, Settings, ThreatIntelCredentials, VirusTotalAvEngines
from polylogyx.utils.intel import check_and_save_intel_alert

from .base import AbstractIntelPlugin


class VTIntel(AbstractIntelPlugin):
    LEVEL_MAPPINGS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    def __init__(self, config):
        self.name = "virustotal"
        levelname = config.get("level", "debug")
        self.vt = None

    def update_credentials(self):
        try:
            credentials = (
                db.session.query(ThreatIntelCredentials)
                .filter(ThreatIntelCredentials.intel_name == "virustotal")
                .first()
            )
            if credentials and "key" in credentials.credentials:
                self.vt = VirusTotalPublicApi(credentials.credentials["key"])
                current_app.logger.info("Virus Total api  configured")
            else:
                self.vt = None
                current_app.logger.warn("Virus Total api not configured")
        except Exception as e:
            current_app.logger.error(e)

    def analyse_hash(self, value, type, node):

        # TODO(andrew-d): better message?
        current_app.logger.log(self.level, " TODO(andrew-d): better message")

    def analyse_pending_hashes(self):

        if self.vt:
            result_log_scans = (
                db.session.query(ResultLogScan)
                .filter(sqlalchemy.not_(ResultLogScan.reputations.has_key(self.name)))
                .filter(ResultLogScan.scan_type.in_(["md5", "sha1", "sha256"]))
                .limit(4)
                .all()
            )
            min_match_count = db.session.query(Settings).filter(Settings.name == "virustotal_min_match_count").first()
            av_engines = [
                item[0]
                for item in db.session.query(VirusTotalAvEngines.name).filter(VirusTotalAvEngines.status == True).all()
            ]
            detected = False
            if len(result_log_scans) > 0:
                scan_values = ",".join([x.scan_value for x in result_log_scans])
                response = self.vt.get_file_report(scan_values)
                if "response_code" in response:
                    if response["response_code"] == requests.codes.ok:
                        scan_reports = response["results"]
                        if len(result_log_scans) == 1:
                            if "positives" in scan_reports:
                                if scan_reports["positives"] > 0:
                                    for avengine in scan_reports["scans"]:
                                        if (
                                            scan_reports["scans"][avengine]["detected"] == True
                                            and avengine in av_engines
                                        ):
                                            detected = True
                                            break
                                    if detected == False and scan_reports["positives"] >= int(min_match_count.setting):
                                        detected = True
                            else:
                                detected = False
                            for result_log_scan_elem in result_log_scans:
                                if result_log_scan_elem.scan_value == scan_reports["resource"]:
                                    result_log_scan_elem.reputations[self.name] = {}
                                    newReputations = dict(result_log_scan_elem.reputations)
                                    newReputations[self.name] = scan_reports
                                    newReputations[self.name + "_detected"] = detected
                                    result_log_scan_elem.reputations = newReputations
                                    result_log_scan_elem.vt_updated_at = dt.datetime.utcnow()
                                    db.session.add(result_log_scan_elem)
                                    break

                        else:
                            for result_log_scan_elem in result_log_scans:
                                for scan_report in scan_reports:
                                    if result_log_scan_elem.scan_value == scan_report["resource"]:
                                        result_log_scan_elem.reputations[self.name] = {}
                                        newReputations = dict(result_log_scan_elem.reputations)
                                        newReputations[self.name] = scan_report
                                        if "positives" in scan_report and scan_report["positives"] > 0:
                                            for avengine in scan_report["scans"]:
                                                if (
                                                    scan_report["scans"][avengine]["detected"] == True
                                                    and avengine in av_engines
                                                ):
                                                    newReputations[self.name + "_detected"] = True
                                                    detected = True
                                                    break
                                            if detected == False and scan_report["positives"] >= int(
                                                min_match_count.setting
                                            ):
                                                newReputations[self.name + "_detected"] = True
                                        else:
                                            newReputations[self.name + "_detected"] = False

                                        result_log_scan_elem.reputations = newReputations
                                        result_log_scan_elem.vt_updated_at=dt.datetime.utcnow()
                                        db.session.add(result_log_scan_elem)
                                        break
                        db.session.commit()
                    elif response["response_code"] == 400:
                        return dict(
                            error="package sent is either malformed or not within the past 24 hours.",
                            response_code=response.status_code,
                        )
                    elif response["response_code"] == 204:
                        return dict(
                            error="You exceeded the public API request rate limit (4 requests of any nature per minute)",
                            response_code=response.status_code,
                        )
                    elif response["response_code"] == 403:
                        return dict(
                            error="You tried to perform calls to functions for which you require a Private API key.",
                            response_code=response.status_code,
                        )
                    elif response["response_code"] == 404:
                        return dict(error="File not found.", response_code=response.status_code)
                    else:
                        return dict(response_code=response.status_code)

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

    # TODO(andrew-d): better message?

    def analyse_domain(self, value, type, node):
        # TODO(andrew-d): better message?
        current_app.logger.log(self.level, "Triggered alert: ")
