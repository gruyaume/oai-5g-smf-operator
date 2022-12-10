# Copyright 2022 Guillaume Belanger
# See LICENSE file for licensing details.

import unittest
from unittest.mock import patch

import ops.testing
from ops.model import ActiveStatus
from ops.testing import Harness

from charm import Oai5GSMFOperatorCharm


class TestCharm(unittest.TestCase):
    @patch(
        "charm.KubernetesServicePatch",
        lambda charm, ports: None,
    )
    def setUp(self):
        ops.testing.SIMULATE_CAN_CONNECT = True
        self.addCleanup(setattr, ops.testing, "SIMULATE_CAN_CONNECT", False)
        self.harness = Harness(Oai5GSMFOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def _create_amf_relation_with_valid_data(self):
        relation_id = self.harness.add_relation("fiveg-amf", "amf")
        self.harness.add_relation_unit(relation_id=relation_id, remote_unit_name="amf/0")

        amf_ipv4_address = "1.2.3.4"
        amf_port = "81"
        amf_api_version = "v1"
        amf_fqdn = "amf.example.com"
        key_values = {
            "amf_ipv4_address": amf_ipv4_address,
            "amf_port": amf_port,
            "amf_fqdn": amf_fqdn,
            "amf_api_version": amf_api_version,
        }
        self.harness.update_relation_data(
            relation_id=relation_id, app_or_unit="amf", key_values=key_values
        )
        return amf_ipv4_address, amf_port, amf_api_version, amf_fqdn

    def _create_upf_relation_with_valid_data(self):
        relation_id = self.harness.add_relation("fiveg-upf", "upf")
        self.harness.add_relation_unit(relation_id=relation_id, remote_unit_name="upf/0")

        upf_ipv4_address = "1.2.3.4"
        upf_fqdn = "upf.example.com"
        key_values = {
            "upf_ipv4_address": upf_ipv4_address,
            "upf_fqdn": upf_fqdn,
        }
        self.harness.update_relation_data(
            relation_id=relation_id, app_or_unit="upf", key_values=key_values
        )
        return upf_ipv4_address, upf_fqdn

    def _create_nrf_relation_with_valid_data(self):
        relation_id = self.harness.add_relation("fiveg-nrf", "nrf")
        self.harness.add_relation_unit(relation_id=relation_id, remote_unit_name="nrf/0")

        nrf_ipv4_address = "1.2.3.4"
        nrf_port = "81"
        nrf_api_version = "v1"
        nrf_fqdn = "nrf.example.com"
        key_values = {
            "nrf_ipv4_address": nrf_ipv4_address,
            "nrf_port": nrf_port,
            "nrf_fqdn": nrf_fqdn,
            "nrf_api_version": nrf_api_version,
        }
        self.harness.update_relation_data(
            relation_id=relation_id, app_or_unit="nrf", key_values=key_values
        )
        return nrf_ipv4_address, nrf_port, nrf_api_version, nrf_fqdn

    def _create_udm_relation_with_valid_data(self):
        relation_id = self.harness.add_relation("fiveg-udm", "udm")
        self.harness.add_relation_unit(relation_id=relation_id, remote_unit_name="udm/0")

        udm_ipv4_address = "1.2.3.4"
        udm_port = "81"
        udm_api_version = "v1"
        udm_fqdn = "udm.example.com"
        key_values = {
            "udm_ipv4_address": udm_ipv4_address,
            "udm_port": udm_port,
            "udm_fqdn": udm_fqdn,
            "udm_api_version": udm_api_version,
        }
        self.harness.update_relation_data(
            relation_id=relation_id, app_or_unit="udm", key_values=key_values
        )
        return udm_ipv4_address, udm_port, udm_api_version, udm_fqdn

    @patch("ops.model.Container.push")
    def test_given_nrf_relation_contains_nrf_info_when_nrf_relation_joined_then_config_file_is_pushed(  # noqa: E501
        self, mock_push
    ):
        self.harness.set_can_connect(container="smf", val=True)
        (
            amf_ipv4_address,
            amf_port,
            amf_api_version,
            amf_fqdn,
        ) = self._create_amf_relation_with_valid_data()
        (
            upf_ipv4_address,
            upf_fqdn,
        ) = self._create_upf_relation_with_valid_data()
        (
            nrf_ipv4_address,
            nrf_port,
            nrf_api_version,
            nrf_fqdn,
        ) = self._create_nrf_relation_with_valid_data()

        (
            udm_ipv4_address,
            udm_port,
            udm_api_version,
            udm_fqdn,
        ) = self._create_udm_relation_with_valid_data()

        mock_push.assert_called_with(
            path="/openair-smf/etc/smf.conf",
            source="################################################################################\n"  # noqa: E501, W505
            "# Licensed to the OpenAirInterface (OAI) Software Alliance under one or more\n"
            "# contributor license agreements.  See the NOTICE file distributed with\n"
            "# this work for additional information regarding copyright ownership.\n"
            "# The OpenAirInterface Software Alliance licenses this file to You under\n"
            '# the OAI Public License, Version 1.1  (the "License"); you may not use this file\n'  # noqa: E501, W505
            "# except in compliance with the License.\n"
            "# You may obtain a copy of the License at\n"
            "#\n"
            "#      http://www.openairinterface.org/?page_id=698\n"
            "#\n"
            "# Unless required by applicable law or agreed to in writing, software\n"
            '# distributed under the License is distributed on an "AS IS" BASIS,\n'
            "# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n"
            "# See the License for the specific language governing permissions and\n"
            "# limitations under the License.\n"
            "#-------------------------------------------------------------------------------\n"  # noqa: E501, W505
            "# For more information about the OpenAirInterface (OAI) Software Alliance:\n"
            "#      contact@openairinterface.org\n"
            "################################################################################\n\n"  # noqa: E501, W505
            "SMF =\n"
            "{\n"
            '    FQDN          = "oai-5g-smf.None.svc.cluster.local";\n'
            "    INSTANCE      = 0;         # 0 is the default\n"
            '    PID_DIRECTORY = "/var/run";  # /var/run is the default\n\n'
            "    INTERFACES :\n"
            "    {\n"
            "        N4 :\n"
            "        {\n"
            "            # SMF binded interface for N4 communication (UPF)\n"
            '            INTERFACE_NAME = "eth0"; # YOUR NETWORK CONFIG HERE\n'
            '            IPV4_ADDRESS   = "read";\n'
            "         };\n\n"
            "        SBI :\n"
            "        {\n"
            "            # SMF binded interface for SBI interface (e.g., communication with AMF, UDM)\n"  # noqa: E501, W505
            '            INTERFACE_NAME = "eth0";     # YOUR NETWORK CONFIG HERE\n'
            '            IPV4_ADDRESS   = "read";\n'
            "            PORT           = 80;       # YOUR NETWORK CONFIG HERE (default: 80)\n"  # noqa: E501, W505
            "            HTTP2_PORT     = 9090; # YOUR NETWORK CONFIG HERE\n"
            '            API_VERSION    = "v1";                # YOUR SMF API VERSION CONFIG HERE\n'  # noqa: E501, W505
            "         };\n\n    };\n\n    # DNN configurations with pool of UE assigned IP addresses\n"  # noqa: E501, W505
            "    # Do not make IP pools overlap\n    # first IPv4 address X.Y.Z.1 is reserved for GTP network device on UPF\n"  # noqa: E501, W505
            "    DNN_LIST = (\n       # PDU_SESSION_TYPE choice in {IPv4, IPv6, IPv4v6}\n"
            '       # DNN IP ADDRESS RANGE format is for example: "12.2.1.2 - 12.2.1.128"\n'
            '      {DNN_NI = "oai.ipv4"; PDU_SESSION_TYPE = "IPv4"; IPV4_RANGE = "12.1.1.2 - 12.1.1.40"; IPV6_PREFIX = "2001:1:2::/64"},\n'  # noqa: E501, W505
            '      {DNN_NI = "default"; PDU_SESSION_TYPE = "IPv4"; IPV4_RANGE = "12.1.1.41 - 12.1.1.80"; IPV6_PREFIX = "3001:1:2::/64"},\n'  # noqa: E501, W505
            '      {DNN_NI = "oai"; PDU_SESSION_TYPE = "IPv4"; IPV4_RANGE = "12.1.1.81 - 12.1.1.120"; IPV6_PREFIX = "4001:1:2::/64"}\n'  # noqa: E501, W505
            "    );\n\n"
            "    # DNS address communicated to UEs\n"
            '    DEFAULT_DNS_IPV4_ADDRESS     = "172.21.3.100";      # YOUR DNS CONFIG HERE\n'  # noqa: E501, W505
            '    DEFAULT_DNS_SEC_IPV4_ADDRESS = "172.21.3.100";  # YOUR DNS CONFIG HERE\n'
            '    DEFAULT_DNS_IPV6_ADDRESS     = "2001:4860:4860::8888";            # YOUR DNS CONFIG HERE\n'  # noqa: E501, W505
            '    DEFAULT_DNS_SEC_IPV6_ADDRESS = "2001:4860:4860::8888";            # YOUR DNS CONFIG HERE\n\n'  # noqa: E501, W505
            "    #Default P-CSCF server\n"
            '    DEFAULT_CSCF_IPV4_ADDRESS = "127.0.0.1";\n'
            '    DEFAULT_CSCF_IPV6_ADDRESS = "fe80::7915:f408:1787:db8b";\n\n'
            "    #Default UE MTU\n"
            "    UE_MTU = 1500;\n\n"
            "    # SUPPORT FEATURES\n"
            "    SUPPORT_FEATURES:\n"
            "    {\n"
            '      # STRING, {"yes", "no"},\n'
            '      REGISTER_NRF = "yes";  # Set to yes if SMF resgisters to an NRF\n'
            '      DISCOVER_UPF = "yes";  # Set to yes to enable UPF discovery and selection\n'  # noqa: E501, W505
            '      FORCE_PUSH_PROTOCOL_CONFIGURATION_OPTIONS = "no"; # Non standard feature, normally should be set to "no",\n'  # noqa: E501, W505
            "                                                        # but you may need to set to yes for UE that do not explicitly request a PDN address through NAS signalling\n"  # noqa: E501, W505
            '      USE_LOCAL_SUBSCRIPTION_INFO = "yes";  # Set to yes if SMF uses local subscription information instead of from an UDM\n'  # noqa: E501, W505
            '      USE_FQDN_DNS = "yes";                  # Set to yes if AMF/UDM/NRF/UPF will relying on a DNS to resolve FQDN\n'  # noqa: E501, W505
            "      HTTP_VERSION = 1;                    # Default: 1\n"
            '      USE_NETWORK_INSTANCE    = "no"   # Set yes if network instance is to be used for given UPF\n'  # noqa: E501, W505
            '      ENABLE_USAGE_REPORTING = "no"   # Set yes if UE USAGE REPORTING is to be done at UPF\n'  # noqa: E501, W505
            "    }\n\n"
            "    AMF :\n"
            "    {\n"
            f'      IPV4_ADDRESS = "{amf_ipv4_address}";  # YOUR AMF CONFIG HERE\n'
            f"      PORT         = {amf_port};            # YOUR AMF CONFIG HERE (default: 80)\n"  # noqa: E501, W505
            f'      API_VERSION  = "{amf_api_version}";   # YOUR AMF API VERSION FOR SBI CONFIG HERE\n'  # noqa: E501, W505
            f'      FQDN         = "{amf_fqdn}"           # YOUR AMF FQDN CONFIG HERE\n'
            '    };\n\n    UDM :\n    {\n      IPV4_ADDRESS = "1.2.3.4";  # YOUR UDM CONFIG HERE\n'  # noqa: E501, W505
            f"      PORT         = {udm_port};            # YOUR UDM CONFIG HERE (default: 80)\n"  # noqa: E501, W505
            f'      API_VERSION  = "{udm_api_version}";   # YOUR UDM API VERSION FOR SBI CONFIG HERE\n'  # noqa: E501, W505
            f'      FQDN         = "{udm_fqdn}"           # YOUR UDM FQDN CONFIG HERE\n'
            '    };\n\n    NRF :\n    {\n      IPV4_ADDRESS = "1.2.3.4";  # YOUR NRF CONFIG HERE\n'  # noqa: E501, W505
            f"      PORT         = {nrf_port};            # YOUR NRF CONFIG HERE (default: 80)\n"  # noqa: E501, W505
            f'      API_VERSION  = "{nrf_api_version}";   # YOUR NRF API VERSION FOR SBI CONFIG HERE\n'  # noqa: E501, W505
            f'      FQDN         = "{nrf_fqdn}"           # YOUR NRF FQDN CONFIG HERE\n'
            "    };\n\n"
            "    UPF_LIST = (\n"
            f'         {{IPV4_ADDRESS = "{upf_ipv4_address}" ; FQDN = "{upf_fqdn}"; NWI_LIST = ({{DOMAIN_ACCESS  = "random", DOMAIN_CORE = "random"}})}}   # YOUR UPF CONFIG HERE\n'  # noqa: E501, W505
            "    );                                                               # NWI_LIST IS OPTIONAL PARAMETER\n\n"  # noqa: E501, W505
            "    LOCAL_CONFIGURATION :\n"
            "    {\n"
            "      SESSION_MANAGEMENT_SUBSCRIPTION_LIST = (\n"
            '         { NSSAI_SST = 1, NSSAI_SD = "1", DNN = "oai.ipv4", DEFAULT_SESSION_TYPE = "IPv4", DEFAULT_SSC_MODE = 1,\n'  # noqa: E501, W505
            '           QOS_PROFILE_5QI = 6, QOS_PROFILE_PRIORITY_LEVEL = 1, QOS_PROFILE_ARP_PRIORITY_LEVEL = 1, QOS_PROFILE_ARP_PREEMPTCAP = "NOT_PREEMPT",\n'  # noqa: E501, W505
            '           QOS_PROFILE_ARP_PREEMPTVULN = "NOT_PREEMPTABLE", SESSION_AMBR_UL = "20Mbps", SESSION_AMBR_DL = "22Mbps"},\n'  # noqa: E501, W505
            '         { NSSAI_SST = 222; NSSAI_SD = "123", DNN = "default", DEFAULT_SESSION_TYPE = "IPv4", DEFAULT_SSC_MODE = 1,\n'  # noqa: E501, W505
            '           QOS_PROFILE_5QI = 7, QOS_PROFILE_PRIORITY_LEVEL = 1, QOS_PROFILE_ARP_PRIORITY_LEVEL = 1, QOS_PROFILE_ARP_PREEMPTCAP = "NOT_PREEMPT",\n'  # noqa: E501, W505
            '           QOS_PROFILE_ARP_PREEMPTVULN = "NOT_PREEMPTABLE", SESSION_AMBR_UL = "20Mbps", SESSION_AMBR_DL = "22Mbps"},\n'  # noqa: E501, W505
            '         { NSSAI_SST = 1; NSSAI_SD = "1023", DNN = "oai", DEFAULT_SESSION_TYPE = "IPv4", DEFAULT_SSC_MODE = 1,\n'  # noqa: E501, W505
            '           QOS_PROFILE_5QI = 8, QOS_PROFILE_PRIORITY_LEVEL = 1, QOS_PROFILE_ARP_PRIORITY_LEVEL = 1, QOS_PROFILE_ARP_PREEMPTCAP = "NOT_PREEMPT",\n'  # noqa: E501, W505
            '           QOS_PROFILE_ARP_PREEMPTVULN = "NOT_PREEMPTABLE", SESSION_AMBR_UL = "20Mbps", SESSION_AMBR_DL = "22Mbps"}\n'  # noqa: E501, W505
            "        );\n"
            "    };\n\n"
            "};",
        )

    @patch("ops.model.Container.push")
    def test_given_nrf_and_db_relation_are_set_when_config_changed_then_pebble_plan_is_created(  # noqa: E501
        self, _
    ):
        self.harness.set_can_connect(container="smf", val=True)
        self._create_amf_relation_with_valid_data()
        self._create_upf_relation_with_valid_data()
        self._create_nrf_relation_with_valid_data()
        self._create_udm_relation_with_valid_data()

        expected_plan = {
            "services": {
                "smf": {
                    "override": "replace",
                    "summary": "smf",
                    "command": "/openair-smf/bin/oai_smf -c /openair-smf/etc/smf.conf -o",
                    "startup": "enabled",
                }
            },
        }
        self.harness.container_pebble_ready("smf")
        updated_plan = self.harness.get_container_pebble_plan("smf").to_dict()
        self.assertEqual(expected_plan, updated_plan)
        service = self.harness.model.unit.get_container("smf").get_service("smf")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())
