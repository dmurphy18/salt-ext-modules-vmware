# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
import uuid
from unittest.mock import MagicMock

import pytest
import salt
import saltext.vmware.modules.esxi as esxi_mod
import saltext.vmware.states.esxi as esxi


@pytest.fixture
def dry_run():
    setattr(esxi, "__opts__", {"test": True})
    yield
    setattr(esxi, "__opts__", {"test": False})


@pytest.fixture
def user_add_error():
    esxi.__salt__["vmware_esxi.add_user"] = MagicMock(
        side_effect=salt.exceptions.SaltException("add error")
    )


@pytest.fixture
def user_update_error():
    esxi.__salt__["vmware_esxi.update_user"] = MagicMock(
        side_effect=salt.exceptions.SaltException("update error")
    )


@pytest.fixture
def user_remove_error():
    esxi.__salt__["vmware_esxi.remove_user"] = MagicMock(
        side_effect=salt.exceptions.SaltException("remove error")
    )


def test_user_present_absent(patch_salt_globals):
    """
    Test scenarios for user_present state run
    """
    user_name = f"A{uuid.uuid4()}"
    random_user = f"Random{uuid.uuid4()}"
    password = "Secret@123"

    # create a new user
    ret = esxi.user_present(name=user_name, password=password)
    assert ret["result"]
    for host in ret["changes"]:
        assert ret["changes"][host]["new"]["name"] == user_name

    # update the user
    ret = esxi.user_present(name=user_name, password=password, description="new desc")
    assert ret["result"]
    for host in ret["changes"]:
        assert ret["changes"][host]["new"]["name"] == user_name
        assert ret["changes"][host]["new"]["description"] == "new desc"

    # Remove the user
    ret = esxi.user_absent(name=user_name)
    assert ret["result"]
    for host in ret["changes"]:
        assert ret["changes"][host][user_name] is True

    # Remove a non-existent user
    ret = esxi.user_absent(name=random_user)
    assert ret["result"] is None
    assert not ret["changes"]


def test_user_add_error(patch_salt_globals, user_add_error):
    """
    Test scenarios for user add error
    """
    user_name = f"A{uuid.uuid4()}"
    password = "Secret@123"
    ret = esxi.user_present(name=user_name, password=password)
    assert ret["result"] is False
    assert not ret["changes"]
    assert "add error" in ret["comment"]


def test_user_remove_error(patch_salt_globals, user_remove_error):
    """
    Test scenarios for user remove error
    """
    # Remove the user
    user_name = f"A{uuid.uuid4()}"
    password = "Secret@123"
    ret = esxi.user_present(name=user_name, password=password)
    assert ret["result"] is True
    ret = esxi.user_absent(name=user_name)
    assert ret["result"] is False
    assert not ret["changes"]
    assert "remove error" in ret["comment"]


def test_user_update_error(patch_salt_globals, user_update_error):
    """
    Test scenarios for user remove error
    """
    # Remove the user
    user_name = f"A{uuid.uuid4()}"
    password = "Secret@123"
    ret = esxi.user_present(name=user_name, password=password)
    assert ret["result"] is True
    ret = esxi.user_present(name=user_name, password=password)
    assert ret["result"] is False
    assert not ret["changes"]
    assert "update error" in ret["comment"]


def test_user_present_absent_dry_run(vmware_datacenter, service_instance, dry_run):
    """
    Test scenarios for vmware_esxi.user_present state run with test=True
    """

    user_name = f"A{uuid.uuid4()}"
    random_user = f"Random{uuid.uuid4()}"
    password = "GVh3J69oMcJ0tA"

    # create a new user
    ret = esxi.user_present(name=user_name, password=password)
    assert ret["result"] is None
    assert not ret["changes"]
    assert ret["comment"].split()[6]

    # update the user
    ret = esxi.user_present(name=user_name, password=password, description="new desc")
    assert ret["result"] is None
    assert not ret["changes"]
    assert ret["comment"].split()[11]

    # Remove the user
    ret = esxi_mod.add_user(
        user_name=user_name, password=password, service_instance=service_instance
    )
    ret = esxi.user_absent(name=user_name)
    assert ret["result"] is None
    assert not ret["changes"]
    assert "will be deleted" in ret["comment"]

    # Remove a non-existent user
    ret = esxi.user_absent(name=random_user)
    assert ret["result"] is None
    assert not ret["changes"]
    assert "will be deleted on 0 host" in ret["comment"]


def test_role_present_absent(patch_salt_globals):
    """
    Test scenarios for role_present state run
    """
    role_name = f"A{uuid.uuid4()}"
    random_role = f"Random{uuid.uuid4()}"

    # create a new role
    ret = esxi.role_present(name=role_name, privilege_ids=["Folder.Create"])
    assert ret["result"]
    assert ret["changes"]["new"]["role_name"] == role_name
    assert ret["changes"]["new"]["privilege_ids"]["added"] == ["Folder.Create"]
    assert not ret["changes"]["new"]["privilege_ids"]["removed"]
    assert "Folder.Create" in ret["changes"]["new"]["privilege_ids"]["current"]

    # update the role
    ret = esxi.role_present(name=role_name, privilege_ids=["Folder.Create", "Folder.Delete"])
    assert ret["result"]
    assert ret["changes"]["new"]["role_name"] == role_name
    assert ret["changes"]["new"]["privilege_ids"]["added"] == ["Folder.Delete"]
    assert not ret["changes"]["new"]["privilege_ids"]["removed"]
    assert "Folder.Delete" in ret["changes"]["new"]["privilege_ids"]["current"]

    # update the role
    ret = esxi.role_present(name=role_name, privilege_ids=["Folder.Delete"])
    assert ret["result"]
    assert ret["changes"]["new"]["role_name"] == role_name
    assert ret["changes"]["new"]["privilege_ids"]["removed"] == ["Folder.Create"]
    assert not ret["changes"]["new"]["privilege_ids"]["added"]
    assert "Folder.Delete" in ret["changes"]["new"]["privilege_ids"]["current"]

    # Remove the role
    ret = esxi.role_absent(name=role_name)
    assert ret["result"]
    assert f"Role {role_name} deleted." == ret["comment"]

    # Remove a non-existent user
    ret = esxi.user_absent(name=random_role)
    assert ret["result"] is None
    assert not ret["changes"]


def test_role_present_absent_dry_run(vmware_datacenter, service_instance, dry_run):
    """
    Test scenarios for vmware_esxi.role_present state run with test=True
    """

    role_name = f"A{uuid.uuid4()}"
    random_role = f"Random{uuid.uuid4()}"

    # create a new role
    ret = esxi.role_present(name=role_name, privilege_ids=["Folder.Create"])
    assert ret["result"] is None
    assert not ret["changes"]
    assert f"Role {role_name} will be created." == ret["comment"]

    # create the role using exec mod
    ret = esxi_mod.add_role(
        role_name=role_name, privilege_ids=["Folder.Create"], service_instance=service_instance
    )
    # update the role
    ret = esxi.role_present(name=role_name, privilege_ids=["Folder.Delete"])
    assert ret["result"] is None
    assert not ret["changes"]
    assert "Folder.Delete privileges will be added" in ret["comment"]
    assert "Folder.Create privileges will be removed" in ret["comment"]

    ret = esxi.role_absent(name=role_name)
    assert ret["result"] is None
    assert not ret["changes"]
    assert f"Role {role_name} will be deleted." == ret["comment"]

    # Remove a non-existent user
    ret = esxi.role_absent(name=random_role)
    assert ret["result"] is None
    assert not ret["changes"]
    assert f"Role {random_role} is not present." in ret["comment"]


def test_vmkernel_adapter_present(vmware_datacenter, service_instance):
    """
    Test add/update/remove a vmkernel adapter
    """
    ret = esxi.vmkernel_adapter_present(
        name=None,
        service_instance=service_instance,
        port_group_name="VMNetwork-PortGroup",
        dvswitch_name="dvSwitch",
        mtu=2000,
        enable_fault_tolerance=True,
        network_type="dhcp",
    )
    assert ret["changes"]
    assert ret["result"]
    for host in ret["changes"]:
        assert ret["changes"][host]

    for host in ret["changes"]:
        update_ret = esxi.vmkernel_adapter_present(
            name=ret["changes"][host],
            datacenter_name="Datacenter",
            service_instance=service_instance,
            port_group_name="VMNetwork-PortGroup",
            dvswitch_name="dvSwitch",
            mtu=2100,
            enable_fault_tolerance=True,
            network_type="dhcp",
            host_name=host,
        )
        assert update_ret
        assert update_ret["result"]
        for host in update_ret["changes"]:
            assert update_ret["changes"][host]

        delete_ret = esxi.vmkernel_adapter_absent(
            name=ret["changes"][host], service_instance=service_instance, host_name=host
        )
        assert delete_ret
        assert delete_ret["result"]
        for host in delete_ret:
            assert delete_ret[host]

    delete_ret = esxi.vmkernel_adapter_absent(
        name="nonexistent",
        service_instance=service_instance,
    )
    assert not delete_ret["result"]
    assert not delete_ret["changes"]


def test_maintenance_mode(patch_salt_globals):
    hosts = list(esxi_mod.get())
    assert hosts
    host = hosts[0]
    try:
        for i in range(3):
            ret = esxi.maintenance_mode(host, True, 120)
            assert ret["result"]
            if not i:
                assert ret["changes"]
            else:
                assert not ret["changes"]
    except Exception as e:
        esxi.maintenance_mode(host, False, 120)
        raise e

    for i in range(3):
        ret = esxi.maintenance_mode(host, False, 120)
        assert ret["result"]
        if not i:
            assert ret["changes"]
        else:
            assert not ret["changes"]


def test_maintenance_mode_dry_run(patch_salt_globals, dry_run):
    hosts = list(esxi_mod.get())
    assert hosts
    host = hosts[0]
    ret = esxi.maintenance_mode(host, True, 120)
    assert ret["result"] is None
    assert ret["changes"]
    assert ret["comment"] == "These options are set to change."


def test_lockdown_mode(patch_salt_globals):
    hosts = list(esxi_mod.get())
    assert hosts
    host = hosts[0]
    try:
        for i in range(3):
            ret = esxi.lockdown_mode(host, True)
            assert ret["result"]
            if not i:
                assert ret["changes"]
            else:
                assert not ret["changes"]
    except Exception as e:
        esxi.lockdown_mode(host, False)
        raise e

    for i in range(3):
        ret = esxi.lockdown_mode(host, False)
        assert ret["result"]
        if not i:
            assert ret["changes"]
        else:
            assert not ret["changes"]


def test_lockdown_mode_dry_run(patch_salt_globals, dry_run):
    hosts = list(esxi_mod.get())
    assert hosts
    host = hosts[0]
    ret = esxi.lockdown_mode(host, True)
    assert ret["result"] is None
    assert ret["changes"]
    assert ret["comment"] == "These options are set to change."


def test_firewall_config_dry_run(patch_salt_globals, dry_run):
    ret = esxi.firewall_config("prod", {"prod": [{"name": "CIMHttpServer", "enabled": True}]})
    assert ret["result"] is None
    assert ret["changes"]
    assert ret["comment"] == "These options are set to change."


def test_firewall_config(patch_salt_globals):
    ret = esxi.firewall_config("prod", {"prod": [{"name": "CIMHttpServer", "enabled": True}]})
    assert ret["result"] is True
    assert ret["changes"]
    assert ret["comment"] == "Configurations have successfully been changed."
    esxi.firewall_config("prod", {"prod": [{"name": "CIMHttpServer", "enabled": False}]})


def test_advanced_config_dry_run(patch_salt_globals, dry_run):
    ret = esxi.advanced_config("Annotations.WelcomeMessage", "hey")
    assert ret["result"] is None
    assert ret["changes"]
    assert ret["comment"] == "These options are set to change."


def test_advanced_config(patch_salt_globals):
    ret = esxi.advanced_config("Annotations.WelcomeMessage", "hey")
    assert ret["result"] is True
    assert ret["changes"]
    assert ret["comment"] == "Configurations have successfully been changed."
    esxi.advanced_config("Annotations.WelcomeMessage", "")


def test_ntp_config_dry_run(patch_salt_globals, dry_run, service_instance):
    ret = esxi.ntp_config(
        name="test",
        service_running=True,
        ntp_servers=["192.174.1.100", "192.174.1.200"],
        service_policy="on",
        service_restart=True,
        service_instance=service_instance,
    )
    assert ret["result"] is None
    assert ret["changes"]
    assert ret["comment"] == "NTP state will change."
    for esxi_server in ret["changes"]:
        assert ret["changes"][esxi_server]["service_running"]["new"] is True
        assert ret["changes"][esxi_server]["ntp_servers"]["new"] == [
            "192.174.1.100",
            "192.174.1.200",
        ]
        assert ret["changes"][esxi_server]["service_policy"]["new"] == "on"
        assert ret["changes"][esxi_server]["service_restart"]["new"] == "NTP Daemon Restarted."


def test_ntp_config(patch_salt_globals, service_instance):
    ret = esxi.ntp_config(
        name="test",
        service_running=True,
        ntp_servers=["192.174.1.100", "192.174.1.200"],
        service_policy="on",
        service_restart=True,
        service_instance=service_instance,
    )
    assert ret["result"] is True
    assert ret["changes"]
    for esxi_server in ret["changes"]:
        assert ret["changes"][esxi_server]["service_running"]["new"] is True
        assert ret["changes"][esxi_server]["ntp_servers"]["new"] == [
            "192.174.1.100",
            "192.174.1.200",
        ]
        assert ret["changes"][esxi_server]["service_policy"]["new"] == "on"
        assert ret["changes"][esxi_server]["service_restart"]["new"] == "NTP Daemon Restarted."
    ret = esxi.ntp_config(
        name="test",
        service_running=True,
        ntp_servers=["192.174.1.100", "192.174.1.200"],
        service_policy="on",
        service_instance=service_instance,
    )
    assert ret["result"] is True
    assert ret["comment"] == "NTP is already in the desired state."
    esxi.ntp_config(
        name="test",
        service_running=False,
        ntp_servers=["192.174.1.101"],
        service_policy="off",
        service_instance=service_instance,
    )


def test_password_present_dry_run(patch_salt_globals, dry_run, service_instance):
    esxi_mod.add_user(user_name="test", password="ThePass1!", service_instance=service_instance)
    ret = esxi.password_present(
        name="test",
        password="TheBigTestPass1!",
        service_instance=service_instance,
    )
    assert ret["result"] is None
    assert ret["comment"] == "Host password will change."
    esxi_mod.remove_user(user_name="test", service_instance=service_instance)


def test_password_present_run(patch_salt_globals, service_instance):
    esxi_mod.add_user(user_name="test", password="ThePass1!", service_instance=service_instance)
    ret = esxi.password_present(
        name="test",
        password="TheBigTestPass1!",
        service_instance=service_instance,
    )
    assert ret["result"] is True
    assert ret["comment"] == "Host password changed."
    esxi_mod.remove_user(user_name="test", service_instance=service_instance)


def test_vsan_config_dry_run(patch_salt_globals, dry_run, service_instance):
    ret = esxi.vsan_config(
        name="test",
        enabled=True,
        service_instance=service_instance,
    )
    assert ret["result"] is None
    assert ret["changes"]
    assert ret["comment"] == "VSAN configuration will change."
    for esxi_server in ret["changes"]:
        assert ret["changes"][esxi_server]["enabled"]["new"] is True


def test_vsan_config(patch_salt_globals, service_instance):
    ret = esxi.vsan_config(
        name="test",
        enabled=True,
        service_instance=service_instance,
    )
    assert ret["result"] is True
    assert ret["changes"]
    for esxi_server in ret["changes"]:
        assert ret["changes"][esxi_server]["enabled"]["new"] is True

    ret = esxi.vsan_config(
        name="test",
        enabled=False,
        service_instance=service_instance,
    )
    assert ret["result"] is True
    assert ret["changes"]
    for esxi_server in ret["changes"]:
        assert ret["changes"][esxi_server]["enabled"]["new"] is False
