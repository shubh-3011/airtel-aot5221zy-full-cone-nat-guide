# Airtel AOT5221ZY Full Cone NAT and Full Feature Guide

Notes from an investigation of an Airtel AOT5221ZY router running firmware `AOT5221ZY_R_2.29`. Results are specific to this device and connection, and may not apply to other firmware or networks.

## Outcome

- The router had separate settings for the global **NAT Full Feature** switch, the WAN **NAT mode**, and the WAN **NAT Type**. Enabling the global switch alone did not change the WAN's symmetric NAT type.
- The active Internet WAN was changed from Symmetric to **Full Cone**. It was later switched from **SUA Only** to **Full Feature**, with mapping set 1.
- With Full Feature enabled, WhatsMyNAT reported **Port Restricted Cone NAT** during one browser test. Separate STUN queries from one local UDP socket produced different public port mappings for different destinations, so the tests did not establish end-to-end full-cone behavior.
- Websites subsequently failed to load for the user. Because the Full Feature mapping set had no configured address-mapping rules and the issue followed that change, the last known-working configuration was restored to **SUA Only + Full Cone**.
- UPnP was then enabled; a temporary UDP mapping was successfully created, queried and removed. UPnP permits LAN devices to request inbound port mappings and should only be used on a trusted network. Another What’s My NAT test reported Port Restricted Cone, while a separate STUN comparison still showed destination-dependent mappings.
- At the user's request, Full Feature and mapping set 1 were enabled again while preserving UPnP. The router reported Full Feature with Full Cone stored, and GitHub loaded immediately afterward. This is a point-in-time test; the earlier connectivity failure could recur, and Wi-Fi and game-specific connectivity were not independently verified.

## Investigation

1. Inspected the router's web pages and JavaScript. The GPON WAN editor displayed a `NATTypeSetIndex` option for Full Cone, but its Apply button was hidden. A direct attempt to invoke its save routine returned HTTP 404 and did not change the setting.
2. Used REA to analyze an extracted copy of the WAN save function. This was static client-side evidence, not a decompilation of the router's server-side firmware; its graph had partial coverage and did not resolve the backend save behavior.
3. Used the router's backup-generation request to obtain an encrypted configuration and inspected the decrypted XML locally. No router backup, decrypted configuration, credentials, session cookies, public addresses, or personal device identifiers are included in this repository.
4. The backup contained an Internet WAN object and references to its `X_5067F0_NATType` and `X_5067F0_FullSetIndex` settings. A candidate configuration adding `X_5067F0_NATType` with the value `FullCone` was encrypted and sent to the router's configuration-restore endpoint. The WAN page subsequently showed Full Cone.
5. A second candidate added `X_5067F0_FullSetIndex` with value `1`. After restoration, the WAN page showed Full Feature and mapping set 1. This was an inferred, device-specific configuration change, not a documented or generally safe procedure. The resulting user-reported connectivity issue led to rollback.

## Configuration details

**Warning:** This procedure can interrupt Internet and voice service, overwrite router settings, or require ISP reprovisioning. The router's usual WAN Apply and backup/restore controls were hidden on the tested firmware. A configuration export may be filtered or incomplete, and a successful restore is not proof that every setting survived. Have the provider and an independently verified recovery method available. Never publish a backup: it can contain passwords and provider credentials.

On the tested firmware, the following is what was done, not a manufacturer-supported recipe:

1. Generate a configuration export using the router's own backup request, and keep the original encrypted backup separate and private. Confirm that the intended restore and recovery procedure is available before making any change.
2. Decrypt the export locally using the format documented in the community backup tool linked below. Do not upload the configuration to any online service. Identify the active Internet PPPoE connection by examining the actual configuration; do not assume the same path on another router.
3. In this case, the object was `InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1`. Its existing interface-setting reference pointed to an `X_5067F0_NATType` field. Adding the following element to that WAN object set the WAN's displayed NAT Type to Full Cone:

   ```xml
   <X_5067F0_NATType PARAMETER="configured" TYPE="string" LENGTH="63">FullCone</X_5067F0_NATType>
   ```

4. The corresponding interface-setting reference pointed to an `X_5067F0_FullSetIndex` field. Adding the following element to the same WAN object selected Full Feature mapping set 1:

   ```xml
   <X_5067F0_FullSetIndex PARAMETER="configured" TYPE="uint32" MAX="4294967295" MIN="0">1</X_5067F0_FullSetIndex>
   ```

   This index and the metadata were inferred from the interface and configuration; they are not verified documentation of the server-side schema. The tested mapping set had no address-mapping rules and was associated with a later browsing outage. Do not assume that selecting an empty set is safe or recommended.

5. Encrypt the candidate in the router's backup format and submit it to the configuration restore endpoint. The router may restart or disconnect clients. Verify the actual WAN mode, NAT type, Internet browsing on both Ethernet and Wi-Fi, and the target game. The tested restore was performed through the device's `/cgi-bin/backupRestore.cgi` endpoint with multipart field `tools_FW_UploadFile` and `postflag=1`.
6. If connectivity fails, restore the separately preserved known-working backup using a verified provider-supported recovery method. Do not assume the web restore interface will remain available after a bad change.

The global **NAT Full Feature** switch, the WAN's **SUA Only / Full Feature** mode, and the WAN's **NAT Type** are separate settings. Full Feature alone is not proof of Open NAT; an upstream NAT or firewall can still restrict traffic.

An HTTP 200 response from a restore request is not proof that a configuration was applied; verify the actual setting and connectivity after any change. Similarly, a web NAT test's result is a point-in-time observation, not a guarantee of behavior for every application or destination.

## Reproducing diagnostics safely

`stun_mapping.py` is a read-only diagnostic that sends STUN binding requests from the same UDP socket to multiple servers and prints their observed public mappings:

```sh
python stun_mapping.py
```

Different mappings across destinations indicate destination-dependent mapping somewhere in the path. Matching mappings alone do not prove full-cone filtering. STUN servers learn the public IP address and port used for the test. UDP or DNS blocking can cause timeouts.

## Safety and limitations

- Keep original router backups private. They can contain PPPoE, Wi-Fi, VoIP, and administrator credentials, and encryption may use a shared device-family secret.
- Do not restore a modified configuration without an independently verified recovery path. It may disconnect clients, overwrite configuration, or require ISP reprovisioning.
- Full Feature address mapping and Full Cone NAT are distinct concepts. Do not assume an empty mapping set is safe or that one setting guarantees the other.
- A WAN IPv4 address different from the externally observed public IPv4 address suggests an upstream translation layer, but does not by itself characterize its complete behavior.
- No firewall disabling, DMZ configuration, firmware installation, or router reboot script is included.

## References

- [REA reverse-engineering toolkit](https://github.com/morluto/rea)
- [Community Zyxel backup tool](https://gist.github.com/ankurpandeyvns/0f72eb73f5724f83b9ceebe079162505) (third-party; inspect before use)
- [What's My NAT](https://whatsmynat.com/)
- [STUN specification, RFC 8489](https://www.rfc-editor.org/rfc/rfc8489)
