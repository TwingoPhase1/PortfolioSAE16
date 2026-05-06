putty = caca, GTKTerm 🔛**🔝**

Voici les tableaux de configuration mis à jour, reflétant strictement l'architecture "Hub & Spoke" (Étoile) demandée (Cœur vers Accès) et la répartition précise des ports configurée dans les scripts.

### 1. Routeur R1 (Cisco 2911)

*Rôle : Porte d'entrée/sortie et routage vers le Cœur.*

| **Interface** | **Type**     | **Adresse IP / Masque** | **Description / Connexion**         |
|-----------|----------|---------------------|---------------------------------|
| **Gi0/0**     | WAN      | **192.168.111.2** /24   | Vers **Box Internet** (Gateway: .1) |
| **Gi0/1**     | LAN (L3) | **10.0.0.1** /30        | Vers **SWR-1** (Lien routé)         |
| Gi0/2     | N/A      | \-                   | *Non utilisé / Shutdown*          |

---

### 2. Switch Cœur SWR-1 (Cisco 3560/3750)

*Rôle : Routage Inter-VLAN, Serveur DHCP, Racine STP, Connexion Serveurs.*

| **Interface**    | **Mode**       | **VLAN / IP**          | **Description / Connexion**                    |
|--------------|------------|--------------------|--------------------------------------------|
| **Gi1/0/1**      | **Port L3**    | **10.0.0.2** /30       | Vers **Routeur R1**                            |
| **Gi1/0/2**      | **Trunk**      | Native 696         | Vers **Proxmox** (VLANs 200, 210...250)        |
| **Gi1/0/21-22**  | **LACP (Po2)** | Trunk (Native 696) | Vers **SW2** (Agrégation 2 Gb/s)               |
| **Gi1/0/23-24**  | **LACP (Po1)** | Trunk (Native 696) | Vers **SW1** (Agrégation 2 Gb/s)               |
| **SVI (Vlan X)** | **Gateway**    | 192.168.**X**.254      | Passerelles (200, 210, 220, 230, 240, 250) |
| Gi1/0/3-20   | Access     | 696                | *Non utilisé / Shutdown (Parking)*           |

---

### 3. Switchs d'Accès SW1 & SW2 (Cisco 2960)

Rôle : Distribution aux utilisateurs et Sécurité (Port Security).

Note : La configuration est identique pour SW1 et SW2, seule l'IP de management change.

| **Interface**   | **Vitesse**  | **Mode**        | **VLAN**       | **Description / Service**               |
|-------------|----------|-------------|------------|-------------------------------------|
| **Gi0/1 - 2**   | **2 Gb/s**   | **Trunk (Po1)** | Native 696 | **Uplink LACP** vers SWR-1              |
| **Fa0/1 - 5**   | 100 Mb/s | Access      | **210**        | Service **Comptabilité**                |
| **Fa0/6 - 10**  | 100 Mb/s | Access      | **220**        | Service **Administratif**               |
| **Fa0/11 - 15** | 100 Mb/s | Access      | **230**        | Service **Vente**                       |
| **Fa0/16 - 18** | 100 Mb/s | Access      | **240**        | Service **Supervision**                 |
| **Fa0/19 - 20** | 100 Mb/s | Access      | **250**        | Service **Admin Info**                  |
| **Fa0/21 - 24** | \-        | Access      | **696**        | **Parking Sécurité** (Shutdown)         |
| **SVI 250**     | \-        | \-           | **250**        | **IP Management** (SW1: .11 / SW2: .12) |

### 4. Résumé des VLANs et Sous-réseaux

| **ID VLAN** | **Nom**          | **Sous-réseau**       | **Utilisation**                          |
|---------|--------------|-------------------|--------------------------------------|
| **200**     | SERVEURS     | 192.168.200.0 /24 | VMs Debian (DNS, Web, SMB)           |
| **210**     | COMPTA       | 192.168.210.0 /24 | PC Comptables                        |
| **220**     | ADMIN        | 192.168.220.0 /24 | PC Administratifs                    |
| **230**     | VENTE        | 192.168.230.0 /24 | PC Commerciaux                       |
| **240**     | SUPERVISION  | 192.168.240.0 /24 | PC Supervision                       |
| **250**     | ADMIN_INFO   | 192.168.250.0 /24 | PC Techs & Management Switchs        |
| **696**     | PARKING_SECU | N/A               | Ports vides et VLAN Natif (Sécurité) |

### Résumé des points clés respectés :

1. **Mots de passe** : `S@E12_Fibre&Co` 
2. **Adressage** : Respect du lien /30 entre R1 et SWR-1 et des VLANs internes /24 pour 150 machines,.
3. **Proxmox** : Configuré sur un port Trunk. Les VMs Debian devront avoir leur interface réseau taguée (ex: eth0.200) ou configurée via le pont Linux `vmbr` correspondant dans Proxmox pour atteindre leur passerelle (ex: 192.168.200.254).
4. **Sécurité** : SSH activé, Telnet désactivé, Ports non utilisés éteints dans le VLAN 696, protection contre les tempêtes de broadcast et BPDU Guard,.

---

### 1. Configuration du Routeur R1 (Cisco 2911)

Routeur Cisco 2911 series 

- Débrancher l'alimentation électrique 
- Rebrancher l'alimentation et 
  - spammer au clavier la combinaison ctrl + break (PAUSE, à côté de arret defil) au démarrage, le mode "rommon" apparaît.

```
confreg 0x2142
reset
```

```
enable
configure terminal
hostname R1

! --- SÉCURITÉ ---
enable secret S@E12_Fibre&Co
service password-encryption
username admin privilege 15 secret S@E12_Fibre&Co
ip domain-name fibre.company
crypto key generate rsa modulus 2048
ip ssh version 2
no ip http server
no ip http secure-server
line vty 0 4
 transport input ssh
 login local
 exec-timeout 5 0
exit

! --- INTERFACES ---
interface GigabitEthernet0/0
 description Vers_WAN_Box
 ip address 192.168.111.2 255.255.255.0
 no shutdown
exit

interface GigabitEthernet0/1
 description Vers_SWR-1_L3
 ip address 10.0.0.1 255.255.255.252
 no shutdown
exit

! --- ROUTAGE (CORRIGÉ) ---
ip route 0.0.0.0 0.0.0.0 192.168.111.1
! Routes vers les VLANs internes via SWR-1 (10.0.0.2)
ip route 192.168.200.0 255.255.255.0 10.0.0.2
ip route 192.168.210.0 255.255.255.0 10.0.0.2
ip route 192.168.220.0 255.255.255.0 10.0.0.2
ip route 192.168.230.0 255.255.255.0 10.0.0.2
ip route 192.168.240.0 255.255.255.0 10.0.0.2
ip route 192.168.250.0 255.255.255.0 10.0.0.2

do write memory
```

---

### 2. Configuration du Switch Cœur SWR-1 (Cisco 3560/3750)

Ce switch est le cœur du réseau : il gère le routage Inter-VLAN, le DHCP et est la racine STP.

```
flash_init
delete flash:config.text
y
delete flash:vlan.dat
y
boot
```

```
eenable
configure terminal
hostname SWR-1

! --- SYSTEME & SECU ---
enable secret S@E12_Fibre&Co
service password-encryption
username admin privilege 15 secret S@E12_Fibre&Co
ip domain-name fibre.company
crypto key generate rsa modulus 2048
ip ssh version 2
ip routing  ! TRES IMPORTANT POUR LE ROUTAGE INTER-VLAN

! --- VLANS ---
vlan 200
 name SERVEURS
vlan 210
 name COMPTA
vlan 220
 name ADMIN
vlan 230
 name VENTE
vlan 240
 name SUPERVISION
vlan 250
 name ADMIN_INFO
vlan 696
 name PARKING_SECU
exit

! --- STP RACINE ---
spanning-tree mode rapid-pvst
spanning-tree vlan 1,200-250,696 root primary

! --- INTERFACE L3 VERS R1 ---
interface GigabitEthernet1/0/1
 description Uplink_Vers_R1
 no switchport
 ip address 10.0.0.2 255.255.255.252
 no shutdown
exit
! Route par défaut vers R1
ip route 0.0.0.0 0.0.0.0 10.0.0.1

! --- PROXMOX ---
interface GigabitEthernet1/0/2
 description Vers_Proxmox_Trunk
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 696
 switchport trunk allowed vlan 200-250,696
 no shutdown
exit

! --- PARKING (SWR-1) ---
interface range GigabitEthernet1/0/3 - 20
 description PARKING
 switchport mode access
 switchport access vlan 696
 shutdown
exit

! --- SVIs (GATEWAYS) ---
interface Vlan 200
 ip address 192.168.200.254 255.255.255.0
 no shutdown
! (Repéter pour les autres VLANs comme dans votre fichier, c'était correct)
interface Vlan 210
 ip address 192.168.210.254 255.255.255.0
 no shutdown

interface Vlan 220
 description GATEWAY_ADMIN
 ip address 192.168.220.254 255.255.255.0
 no shutdown

interface Vlan 230
 description GATEWAY_VENTE
 ip address 192.168.230.254 255.255.255.0
 no shutdown

interface Vlan 240
 description GATEWAY_SUPERVISION
 ip address 192.168.240.254 255.255.255.0
 no shutdown

interface Vlan 250
 description GATEWAY_ADMIN_INFO
 ip address 192.168.250.254 255.255.255.0
 no shutdown

! --- DHCP ---
! Exclusion des IPs passerelles
ip dhcp excluded-address 192.168.200.254
ip dhcp excluded-address 192.168.210.254
ip dhcp excluded-address 192.168.220.254
ip dhcp excluded-address 192.168.230.254
ip dhcp excluded-address 192.168.240.254
ip dhcp excluded-address 192.168.250.254
ip dhcp excluded-address 192.168.250.11
ip dhcp excluded-address 192.168.250.12

! POOL COMPTA
ip dhcp pool POOL_COMPTA
 network 192.168.210.0 255.255.255.0
 default-router 192.168.210.254
 dns-server 192.168.200.10 192.168.111.1

! POOL ADMIN (220)
ip dhcp pool POOL_ADMIN
 network 192.168.220.0 255.255.255.0
 default-router 192.168.220.254
 dns-server 192.168.200.10 192.168.111.1

! POOL VENTE (230)
ip dhcp pool POOL_VENTE
 network 192.168.230.0 255.255.255.0
 default-router 192.168.230.254
 dns-server 192.168.200.10 192.168.111.1

! POOL SUPERVISION (240)
ip dhcp pool POOL_SUPERVISION
 network 192.168.240.0 255.255.255.0
 default-router 192.168.240.254
 dns-server 192.168.200.10 192.168.111.1

! POOL ADMIN_INFO (250)
ip dhcp pool POOL_ADMIN_INFO
 network 192.168.250.0 255.255.255.0
 default-router 192.168.250.254
 dns-server 192.168.200.10 192.168.111.1

! --- LACP & TRUNKS ---
! Vers SW1 (Utiliser channel-group 1)
interface range GigabitEthernet1/0/23 - 24
 channel-group 1 mode active
 no shutdown
exit

interface Port-channel 1
 description Vers_SW1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 696
 switchport trunk allowed vlan 200-250,696
 no shutdown
exit

! Vers SW2 (Utiliser channel-group 2)
interface range GigabitEthernet1/0/21 - 22
 channel-group 2 mode active
 no shutdown
exit

interface Port-channel 2
 description Vers_SW2
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 696
 switchport trunk allowed vlan 200-250,696
 no shutdown
exit

do write memory
```

---

### 3. Commutateur d'Accès : SW1 (Cisco 2960)

```
flash_init
delete flash:config.text
y
delete flash:vlan.dat
y
boot
```

```
enable
configure terminal
hostname SW1

! --- SECU BASE ---
enable secret S@E12_Fibre&Co
service password-encryption
username admin privilege 15 secret S@E12_Fibre&Co
ip domain-name fibre.company
crypto key generate rsa modulus 2048
ip ssh version 2

! --- CREATION VLANS (Indispensable sur l'accès aussi) ---
vlan 200
 name SERVEURS
vlan 210
 name COMPTA
vlan 220
 name ADMIN
vlan 230
 name VENTE
vlan 240
 name SUPERVISION
vlan 250
 name ADMIN_INFO
vlan 696
 name PARKING_SECU
exit

! --- UPLINK LACP ---
interface range GigabitEthernet0/1 - 2
 description Vers_SWR-1
 channel-group 1 mode active
 no shutdown
exit

interface Port-channel 1
 switchport mode trunk
 switchport trunk native vlan 696
 switchport trunk allowed vlan 200-250,696
 no shutdown
exit

! --- PORTS UTILISATEURS (Exemple Compta) ---
interface range FastEthernet0/1 - 5
 description PC_COMPTA
 switchport mode access
 switchport access vlan 210
 spanning-tree portfast
 ! Sécurité
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
 storm-control broadcast level 5.0
 no shutdown
exit

! --- PORTS ADMIN (VLAN 220) ---
interface range FastEthernet0/6 - 10
 description PC_ADMIN
 switchport mode access
 switchport access vlan 220
 spanning-tree portfast
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
 storm-control broadcast level 5.0
 no shutdown
exit

! --- PORTS VENTE (VLAN 230) ---
interface range FastEthernet0/11 - 15
 description PC_VENTE
 switchport mode access
 switchport access vlan 230
 spanning-tree portfast
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
 storm-control broadcast level 5.0
 no shutdown
exit

! --- PORTS SUPERVISION (VLAN 240) ---
interface range FastEthernet0/16 - 18
 description PC_SUPERVISION
 switchport mode access
 switchport access vlan 240
 spanning-tree portfast
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
 storm-control broadcast level 5.0
 no shutdown
exit

! --- PORTS ADMIN_INFO (VLAN 250) ---
interface range FastEthernet0/19 - 20
 description PC_ADMIN_INFO
 switchport mode access
 switchport access vlan 250
 spanning-tree portfast
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
 storm-control broadcast level 5.0
 no shutdown
exit

! --- PORTS PARKING ---
interface range FastEthernet0/21 - 24
 description PORT_INACTIF
 switchport mode access
 switchport access vlan 696
 shutdown
 spanning-tree bpduguard enable
exit

! --- MANAGEMENT ---
interface Vlan 250
 ip address 192.168.250.11 255.255.255.0
 no shutdown
exit
ip default-gateway 192.168.250.254

do write memory
```

### 4. Commutateur d'Accès : SW2 (Cisco 2960)

```
flash_init
delete flash:config.text
y
delete flash:vlan.dat
y
boot
```

```
eenable
configure terminal
hostname SW2

! --- SECU BASE ---
enable secret S@E12_Fibre&Co
service password-encryption
username admin privilege 15 secret S@E12_Fibre&Co
ip domain-name fibre.company
crypto key generate rsa modulus 2048
ip ssh version 2

! --- CREATION VLANS (Indispensable sur l'accès aussi) ---
vlan 200
 name SERVEURS
vlan 210
 name COMPTA
vlan 220
 name ADMIN
vlan 230
 name VENTE
vlan 240
 name SUPERVISION
vlan 250
 name ADMIN_INFO
vlan 696
 name PARKING_SECU
exit

! --- UPLINK LACP ---
interface range GigabitEthernet0/1 - 2
 description Vers_SWR-1
 channel-group 1 mode active
 no shutdown
exit

interface Port-channel 1
 switchport mode trunk
 switchport trunk native vlan 696
 switchport trunk allowed vlan 200-250,696
 no shutdown
exit

! --- PORTS UTILISATEURS ---

! COMPTA (210)
interface range FastEthernet0/1 - 5
 description PC_COMPTA
 switchport mode access
 switchport access vlan 210
 spanning-tree portfast
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
 storm-control broadcast level 5.0
 no shutdown
exit

! ADMIN (220)
interface range FastEthernet0/6 - 10
 description PC_ADMIN
 switchport mode access
 switchport access vlan 220
 spanning-tree portfast
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
 storm-control broadcast level 5.0
 no shutdown
exit

! VENTE (230)
interface range FastEthernet0/11 - 15
 description PC_VENTE
 switchport mode access
 switchport access vlan 230
 spanning-tree portfast
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
 storm-control broadcast level 5.0
 no shutdown
exit

! SUPERVISION (240)
interface range FastEthernet0/16 - 18
 description PC_SUPERVISION
 switchport mode access
 switchport access vlan 240
 spanning-tree portfast
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
 storm-control broadcast level 5.0
 no shutdown
exit

! ADMIN_INFO (250)
interface range FastEthernet0/19 - 20
 description PC_ADMIN_INFO
 switchport mode access
 switchport access vlan 250
 spanning-tree portfast
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
 storm-control broadcast level 5.0
 no shutdown
exit

! --- PORTS PARKING ---
interface range FastEthernet0/21 - 24
 description PORT_INACTIF
 switchport mode access
 switchport access vlan 696
 shutdown
 spanning-tree bpduguard enable
exit

! --- MANAGEMENT ---
interface Vlan 250
 ip address 192.168.250.12 255.255.255.0
 no shutdown
exit
ip default-gateway 192.168.250.254

do write memory
```