# AOT5221ZY NAT investigation

Notes from an investigation of an Airtel AOT5221ZY router running firmware `AOT5221ZY_R_2.29`. Results are specific to this device and connection, and may not apply to other firmware or networks.

## Outcome

- The router had separate settings for the global **NAT Full Feature** switch, the WAN **NAT mode**, and the WAN **NAT Type**. Enabling the global switch alone did not change the WAN's symmetric NAT type.
- The active Internet WAN was changed from Symmetric to **Full Cone**. It was later switched from **SUA Only** to **Full Feature**, with mapping set 1.
- With Full Feature enabled, WhatsMyNAT reported **Port Restricted Cone NAT** during one browser test. Separate STUN queries from one local UDP socket produced different public port mappings for different destinations, so the tests did not establish end-to-end full-cone behavior.
- Websites subsequently failed to load for the user. Because the Full Feature mapping set had no configured address-mapping rules and the issue followed that change, the last known-working configuration was restored. The final verified WAN state was **SUA Only + Full Cone**. Ethernet access to GitHub worked after rollback; Wi-Fi and long-term stability were not independently verified.

## Investigation

1. Inspected the router's web pages and JavaScript. The GPON WAN editor displayed a `NATTypeSetIndex` option for Full Cone, but its Apply button was hidden. A direct attempt to invoke its save routine returned HTTP 404 and did not change the setting.
2. Used REA to analyze an extracted copy of the WAN save function. This was static client-side evidence, not a decompilation of the router's server-side firmware; its graph had partial coverage and did not resolve the backend save behavior.
3. Used the router's backup-generation request to obtain an encrypted configuration and inspected the decrypted XML locally. No router backup, decrypted configuration, credentials, session cookies, public addresses, or personal device identifiers are included in this repository.
4. The backup contained an Internet WAN object and references to its `X_5067F0_NATType` and `X_5067F0_FullSetIndex` settings. A candidate configuration adding `X_5067F0_NATType` with the value `FullCone` was encrypted and sent to the router's configuration-restore endpoint. The WAN page subsequently showed Full Cone.
5. A second candidate added `X_5067F0_FullSetIndex` with value `1`. After restoration, the WAN page showed Full Feature and mapping set 1. This was an inferred, device-specific configuration change, not a documented or generally safe procedure. The resulting user-reported connectivity issue led to rollback.

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
