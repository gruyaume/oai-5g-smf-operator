#!/usr/bin/env python3
# Copyright 2022 Guillaume Belanger
# See LICENSE file for licensing details.

"""Charmed Operator for the OpenAirInterface 5G Core SMF component."""


import logging

from charms.oai_5g_amf.v0.fiveg_amf import FiveGAMFRequires  # type: ignore[import]
from charms.oai_5g_nrf.v0.fiveg_nrf import FiveGNRFRequires  # type: ignore[import]
from charms.oai_5g_udm.v0.oai_5g_udm import FiveGUDMRequires  # type: ignore[import]
from charms.oai_5g_upf.v0.fiveg_upf import FiveGUPFRequires  # type: ignore[import]
from charms.observability_libs.v1.kubernetes_service_patch import (  # type: ignore[import]
    KubernetesServicePatch,
    ServicePort,
)
from jinja2 import Environment, FileSystemLoader
from ops.charm import CharmBase, ConfigChangedEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus

logger = logging.getLogger(__name__)

BASE_CONFIG_PATH = "/openair-smf/etc"
CONFIG_FILE_NAME = "smf.conf"


class Oai5GSMFOperatorCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        """Observes juju events."""
        super().__init__(*args)
        self._container_name = "smf"
        self._container = self.unit.get_container(self._container_name)
        self.service_patcher = KubernetesServicePatch(
            charm=self,
            ports=[
                ServicePort(
                    name="oai-smf",
                    port=8805,
                    protocol="UDP",
                    targetPort=8805,
                ),
                ServicePort(
                    name="http1",
                    port=int(self._config_sbi_interface_port),
                    protocol="TCP",
                    targetPort=int(self._config_sbi_interface_port),
                ),
                ServicePort(
                    name="http2",
                    port=int(self._config_sbi_interface_http2_port),
                    protocol="TCP",
                    targetPort=int(self._config_sbi_interface_http2_port),
                ),
            ],
        )
        self.amf_requires = FiveGAMFRequires(self, "fiveg-amf")
        self.upf_requires = FiveGUPFRequires(self, "fiveg-upf")
        self.nrf_requires = FiveGNRFRequires(self, "fiveg-nrf")
        self.udm_requires = FiveGUDMRequires(self, "fiveg-udm")
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.fiveg_amf_relation_changed, self._on_config_changed)
        self.framework.observe(self.on.fiveg_upf_relation_changed, self._on_config_changed)
        self.framework.observe(self.on.fiveg_nrf_relation_changed, self._on_config_changed)
        self.framework.observe(self.on.fiveg_udm_relation_changed, self._on_config_changed)

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Triggered on any change in configuration.

        Args:
            event: Config Changed Event

        Returns:
            None
        """
        if not self._container.can_connect():
            self.unit.status = WaitingStatus("Waiting for Pebble in workload container")
            event.defer()
            return
        if not self._amf_relation_created:
            self.unit.status = BlockedStatus("Waiting for relation to AMF to be created")
            return
        if not self._upf_relation_created:
            self.unit.status = BlockedStatus("Waiting for relation to UPF to be created")
            return
        if not self._nrf_relation_created:
            self.unit.status = BlockedStatus("Waiting for relation to NRF to be created")
            return
        if not self._udm_relation_created:
            self.unit.status = BlockedStatus("Waiting for relation to UDM to be created")
            return
        if not self.amf_requires.amf_ipv4_address_available:
            self.unit.status = WaitingStatus(
                "Waiting for AMF IPv4 address to be available in relation data"
            )
            return
        if not self.upf_requires.upf_ipv4_address_available:
            self.unit.status = WaitingStatus(
                "Waiting for UPF IPv4 address to be available in relation data"
            )
            return
        if not self.nrf_requires.nrf_ipv4_address_available:
            self.unit.status = WaitingStatus(
                "Waiting for NRF IPv4 address to be available in relation data"
            )
            return
        if not self.udm_requires.udm_ipv4_address_available:
            self.unit.status = WaitingStatus(
                "Waiting for UDM IPv4 address to be available in relation data"
            )
            return
        self._push_config()
        self._update_pebble_layer()
        self.unit.status = ActiveStatus()

    def _update_pebble_layer(self) -> None:
        """Updates pebble layer with new configuration.

        Returns:
            None
        """
        self._container.add_layer("smf", self._pebble_layer, combine=True)
        self._container.replan()
        self.unit.status = ActiveStatus()

    @property
    def _amf_relation_created(self) -> bool:
        return self._relation_created("fiveg-amf")

    @property
    def _upf_relation_created(self) -> bool:
        return self._relation_created("fiveg-upf")

    @property
    def _nrf_relation_created(self) -> bool:
        return self._relation_created("fiveg-nrf")

    @property
    def _udm_relation_created(self) -> bool:
        return self._relation_created("fiveg-udm")

    def _relation_created(self, relation_name: str) -> bool:
        if not self.model.get_relation(relation_name):
            return False
        return True

    def _push_config(self) -> None:
        jinja2_environment = Environment(loader=FileSystemLoader("src/templates/"))
        template = jinja2_environment.get_template(f"{CONFIG_FILE_NAME}.j2")
        content = template.render(
            fqdn=self._config_fqdn,
            instance=self._config_instance,
            pid_directory=self._config_pid_directory,
            n4_interface_name=self._config_n4_interface_name,
            sbi_interface_name=self._config_sbi_interface_name,
            sbi_interface_port=self._config_sbi_interface_port,
            sbi_interface_http2_port=self._config_sbi_interface_http2_port,
            sbi_interface_api_version=self._config_sbi_interface_api_version,
            dnn_0_ni=self._config_dnn_0_ni,
            dnn_0_pdu_session_type=self._config_dnn_0_pdu_session_type,
            dnn_0_ipv4_range=self._config_dnn_0_ipv4_range,
            dnn_0_ipv6_prefix=self._config_dnn_0_ipv6_prefix,
            dnn_1_ni=self._config_dnn_1_ni,
            dnn_1_pdu_session_type=self._config_dnn_1_pdu_session_type,
            dnn_1_ipv4_range=self._config_dnn_1_ipv4_range,
            dnn_1_ipv6_prefix=self._config_dnn_1_ipv6_prefix,
            dnn_2_ni=self._config_dnn_2_ni,
            dnn_2_pdu_session_type=self._config_dnn_2_pdu_session_type,
            dnn_2_ipv4_range=self._config_dnn_2_ipv4_range,
            dnn_2_ipv6_prefix=self._config_dnn_2_ipv6_prefix,
            dns_0_ipv4_address=self._config_dns_0_ipv4_address,
            dns_1_ipv4_address=self._config_dns_1_ipv4_address,
            dns_0_ipv6_address=self._config_dns_0_ipv6_address,
            dns_1_ipv6_address=self._config_dns_1_ipv6_address,
            ue_mtu=self._config_ue_mtu,
            register_nrf=self._config_register_nrf,
            discover_upf=self._config_discover_upf,
            use_local_subscription_info=self._config_use_local_subscription_info,
            use_fqdn_dns=self._config_use_fqdn_dns,
            http_version=self._config_http_version,
            use_network_instance=self._config_use_network_instance,
            enable_usage_reporting=self._config_enable_usage_reporting,
            amf_ipv4_address=self.amf_requires.amf_ipv4_address,
            amf_port=self.amf_requires.amf_port,
            amf_api_version=self.amf_requires.amf_api_version,
            amf_fqdn=self.amf_requires.amf_fqdn,
            udm_ipv4_address=self.udm_requires.udm_ipv4_address,
            udm_port=self.udm_requires.udm_port,
            udm_api_version=self.udm_requires.udm_api_version,
            udm_fqdn=self.udm_requires.udm_fqdn,
            nrf_ipv4_address=self.nrf_requires.nrf_ipv4_address,
            nrf_port=self.nrf_requires.nrf_port,
            nrf_api_version=self.nrf_requires.nrf_api_version,
            nrf_fqdn=self.nrf_requires.nrf_fqdn,
            upf_0_ipv4_address=self.upf_requires.upf_ipv4_address,
            upf_0_fqdn=self.upf_requires.upf_fqdn,
            upf_0_nwi_0_domain_access=self._config_domain_access,
            upf_0_nwi_0_domain_core=self._config_core_access,
            session_management_0_nssai_sst=self._config_dnn_0_nssai_sst,
            session_management_0_nssai_sd=self._config_dnn_0_nssai_sd,
            session_management_0_dnn=self._config_dnn_0_ni,
            session_management_0_default_session_type=self._config_dnn_0_pdu_session_type,
            session_management_1_nssai_sst=self._config_dnn_1_nssai_sst,
            session_management_1_nssai_sd=self._config_dnn_1_nssai_sd,
            session_management_1_dnn=self._config_dnn_1_ni,
            session_management_1_default_session_type=self._config_dnn_0_pdu_session_type,
            session_management_2_nssai_sst=self._config_dnn_2_nssai_sst,
            session_management_2_nssai_sd=self._config_dnn_2_nssai_sd,
            session_management_2_dnn=self._config_dnn_2_ni,
            session_management_2_default_session_type=self._config_dnn_0_pdu_session_type,
        )

        self._container.push(path=f"{BASE_CONFIG_PATH}/{CONFIG_FILE_NAME}", source=content)
        logger.info(f"Wrote file to container: {CONFIG_FILE_NAME}")

    @property
    def _config_file_is_pushed(self) -> bool:
        """Check if config file is pushed to the container."""
        if not self._container.exists(f"{BASE_CONFIG_PATH}/{CONFIG_FILE_NAME}"):
            logger.info(f"Config file is not written: {CONFIG_FILE_NAME}")
            return False
        logger.info("Config file is pushed")
        return True

    @property
    def _config_instance(self) -> str:
        return "0"

    @property
    def _config_pid_directory(self) -> str:
        return "/var/run"

    @property
    def _config_fqdn(self) -> str:
        return f"{self.model.app.name}.{self.model.name}.svc.cluster.local"

    @property
    def _config_n4_interface_name(self) -> str:
        return "eth0"

    @property
    def _config_sbi_interface_name(self) -> str:
        return "eth0"

    @property
    def _config_sbi_interface_port(self) -> str:
        return "80"

    @property
    def _config_sbi_interface_http2_port(self) -> str:
        return "9090"

    @property
    def _config_sbi_interface_api_version(self) -> str:
        return "v1"

    @property
    def _config_dnn_0_ni(self) -> str:
        return "oai.ipv4"

    @property
    def _config_dnn_0_pdu_session_type(self) -> str:
        return "IPv4"

    @property
    def _config_dnn_0_ipv4_range(self) -> str:
        return "12.1.1.2 - 12.1.1.40"

    @property
    def _config_dnn_0_ipv6_prefix(self) -> str:
        return "2001:1:2::/64"

    @property
    def _config_dnn_1_ni(self) -> str:
        return "default"

    @property
    def _config_dnn_1_pdu_session_type(self) -> str:
        return "IPv4"

    @property
    def _config_dnn_1_ipv4_range(self) -> str:
        return "12.1.1.41 - 12.1.1.80"

    @property
    def _config_dnn_1_ipv6_prefix(self) -> str:
        return "3001:1:2::/64"

    @property
    def _config_dnn_2_ni(self) -> str:
        return "oai"

    @property
    def _config_dnn_2_pdu_session_type(self) -> str:
        return "IPv4"

    @property
    def _config_dnn_2_ipv4_range(self) -> str:
        return "12.1.1.81 - 12.1.1.120"

    @property
    def _config_dnn_2_ipv6_prefix(self) -> str:
        return "4001:1:2::/64"

    @property
    def _config_dns_0_ipv4_address(self) -> str:
        return "172.21.3.100"

    @property
    def _config_dns_0_ipv6_address(self) -> str:
        return "2001:4860:4860::8888"

    @property
    def _config_dns_1_ipv4_address(self) -> str:
        return "172.21.3.100"

    @property
    def _config_dns_1_ipv6_address(self) -> str:
        return "2001:4860:4860::8888"

    @property
    def _config_ue_mtu(self) -> str:
        return "1500"

    @property
    def _config_register_nrf(self) -> str:
        return "yes"

    @property
    def _config_discover_upf(self) -> str:
        return "yes"

    @property
    def _config_use_local_subscription_info(self) -> str:
        return "yes"

    @property
    def _config_use_fqdn_dns(self) -> str:
        return "yes"

    @property
    def _config_http_version(self) -> str:
        return "1"

    @property
    def _config_use_network_instance(self) -> str:
        return "no"

    @property
    def _config_enable_usage_reporting(self) -> str:
        return "no"

    @property
    def _config_domain_access(self) -> str:
        return "random"

    @property
    def _config_core_access(self) -> str:
        return "random"

    @property
    def _config_dnn_0_nssai_sst(self) -> str:
        return "1"

    @property
    def _config_dnn_0_nssai_sd(self) -> str:
        return "1"

    @property
    def _config_dnn_1_nssai_sst(self) -> str:
        return "222"

    @property
    def _config_dnn_1_nssai_sd(self) -> str:
        return "123"

    @property
    def _config_dnn_2_nssai_sst(self) -> str:
        return "1"

    @property
    def _config_dnn_2_nssai_sd(self) -> str:
        return "1023"

    @property
    def _pebble_layer(self) -> dict:
        """Return a dictionary representing a Pebble layer."""
        return {
            "summary": "smf layer",
            "description": "pebble config layer for smf",
            "services": {
                "smf": {
                    "override": "replace",
                    "summary": "smf",
                    "command": f"/openair-smf/bin/oai_smf -c {BASE_CONFIG_PATH}/{CONFIG_FILE_NAME} -o",  # noqa: E501
                    "startup": "enabled",
                }
            },
        }


if __name__ == "__main__":
    main(Oai5GSMFOperatorCharm)
