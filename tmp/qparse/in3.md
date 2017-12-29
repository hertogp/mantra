---
exam_number: 200-125
passing_score: 800
time_limit: 120 min
version: 1.0
exam_name: Cisco Certified Network Associate Exam, 200-125
file_name: Cisco.Testking.200-125.v2016-06-29.by.Ray.43q--paypal.pdf
...

# Q1
In which two formats can the IPv6 address
fd15:0db8:0000:0000:0700:0003:400F:572B be written? (Choose two.)

a. fd15:0db8:0000:0000:700:3:400F:527B
b. fd15::db8::700:3:400F:527B
c. fd15:db8:0::700:3:4F:527B
d. fd15:0db8::7:3:4F:527B
e. fd15:db8::700:3:400F:572B

Answer: AE

Section: ipv6

Explanation:

# Q2
When an interface is configured with PortFast BPDU guard, how does the
interface respond when it receives a BPDU?

a. It continues operating normally.
b. It goes into a down/down state.
c. It becomes the root bridge for the configured VLAN.
d. It goes into an errdisable state.

Answer: D

Section: stp

Explanation:

# Q3
What are three characteristics of the TCP protocol? (Choose three.)

a. It uses a single SYN-ACK message to establish a connection.
b. The connection is established before data is transmitted.
c. It ensures that all data is transmitted and received by the remote device.
d. It supports significantly higher transmission speeds than UDP.
e. It requires applications to determine when data packets must be retransmitted.
f. It uses separate SYN and ACK messages to establish a connection.

Answer: B,C,F

Section: L4

Explanation:

# Q4
Refer to the topology. Your company has decided to connect the main office with
three other remote branch offices using point-to-point serial links. You are
required to troubleshoot and resolve OSPF neighbor adjacency issues between the
main office and the routers located in the remote branch offices. Use
appropriate show commands to troubleshoot the issues and answer all four
questions. Instructions

![topology](img/img-003-000.png)

An OSPF neighbor adjacency is not formed between R3 in the main office and R4
in the Branch1 office. What is causing the problem?

a. There is an area ID mismatch.
b. There is a Layer 2 issue; an encapsulation mismatch on serial links.
c. There is an OSPF hello and dead interval mismatch.
d. The R3 router ID is configured on R4.

On both R3 and R4 use “show running-config” command to check their S1/0 interfaces

```bash
R3#show running-config
\<\<output omitted\>\>
!
interface Serial1/0
  description \*\*Connected to R4-Branch1 office\*\*
  ip address 10.10.240.1 255.255.255.252
  encapsulation ppp
  ip ospf 3 area 0
!
\<\<output omitted\>\>

R4#show running-config
\<\<output omitted\>\>
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.2 255.255.255.252
 encapsulation ppp
 ip ospf 4 area 2
!
\<\<output omitted\>\>
```

Answer: A

Section: ospf

Explanation:
Here are the relevant parts of the router configs:

```cisco
R1
!
interface Loopback0
  description \*\*\*Loopback\*\*\*
  ip address 192.168.1.1 255.255.255.255
  ip ospf 1 area 0
!
interface Ethernet0/0
  description \*\*Connected to R1-LAN\*\*
  ip address 10.10.110.1 255.255.255.0
  ip ospf 1 area 0
!
interface Ethernet0/1
  description \*\*Connected to L2SW\*\*
  ip address 10.10.230.1 255.255.255.0
  ip ospf hello-interval 25
  ip ospf 1 area 0
!
router ospf 1
  log-adjacency-changes

R2
!
interface Loopback0
  description \*\*Loopback\*\*
  ip address 192.168.2.2 255.255.255.255
  ip ospf 2 area 0
!
interface Ethernet0/0
  description \*\*Connected to R2-LAN\*\*
  ip address 10.10.120.1 255.255.255.0
  ip ospf 2 area 0
!
interface Ethernet0/1
  description \*\*Connected to L2SW\*\*
  ip address 10.10.230.2 255.255.255.0
  ip ospf 2 area 0
!
router ospf 2
  logadjacency-changes

R3
!
username R6 password CISCO36
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.3.3 255.255.255.255
 ip ospf 3 area 0
!
interface Ethernet0/0
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.3 255.255.255.0
 ip ospf 3 area 0
!
interface Serial1/0
 description \*\*Connected to R4-Branch1 office\*\*
 ip address 10.10.240.1 255.255.255.252
 encapsulation ppp
 ip ospf 3 area 0
!
interface Serial1/1
 description \*\*Connected to R5-Branch2 office\*\*
 ip address 10.10.240.5 255.255.255.252
 encapsulation ppp
 ip ospf hello-interval 50
 ip ospf 3 area 0
!
interface Serial1/2
 description \*\*Connected to R6-Branch3 office\*\*
 ip address 10.10.240.9 255.255.255.252
 encapsulation ppp
 ip ospf 3 area 0ppp authentication chap
!
router
 ospf 3
 router-id 192.168.3.3
!
end

R4
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.4.4 255.255.255.255
 ip ospf 4 area 2
!
interface Ethernet0/0
 ip address 172.16.113.1 255.255.255.0
 ip ospf 4 area 2
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.2 255.255.255.252
 encapsulation ppp
 ip ospf 4 area 2
!
router ospf 4
 log-adjacencychanges
!
end

R5
!
interface Loopback0descr iption \*\*Loopback\*\*
 ip address 192.168.5.5 255.255.255.255
 ip ospf 5 area 0
!
interface Ethernet0/0
 ip address 172.16.114.1 255.255.255.0
 ip ospf 5 area 0
!
interface Serial1/0descr iption \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.6 255.255.255.252
 encapsulation ppp
 ip ospf 5 area 0
!
router ospf 5
 log-adjacencychanges


R6
!
username R3 password CISCO36
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.6.6 255.255.255.255
 ip ospf 6 area 0
!
interface Ethernet0/0
 ip address 172.16.115.1 255.255.255.0
 ip ospf 6 area 0
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.10 255.255.255.252
 encapsulation ppp
 ip ospf 6 area 0
 ppp authentication chap
!
router ospf 6
 router-id 192.168.3.3
!
end
```

On both R3 and R4 use “show running-config” command to check their S1/0 interfaces

```
R3#show running-config
\<\<output omitted\>\>
!
interface Serial1/0
  description \*\*Connected to R4-Branch1 office\*\*
  ip address 10.10.240.1 255.255.255.252
  encapsulation ppp
  ip ospf 3 area 0
!
\<\<output omitted\>\>

R4#show running-config
\<\<output omitted\>\>
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.2 255.255.255.252
 encapsulation ppp
 ip ospf 4 area 2
!
\<\<output omitted\>\>
```

In the output above we see their Area IDs are mismatched; interface S1/0 of R3
is in area 0 (R3: ip ospf 3 area 0) while interface s1/0 of R4 is in area 2
(R4: ip ospf 4 area 2).

# Q5

Refer to the topology. Your company has decided to connect the main office with
three other remote branch offices using point-to-point serial links. You are
required to troubleshoot and resolve OSPF neighbor adjacency issues between the
main office and the routers located in the remote branch offices. Use
appropriate show commands to troubleshoot the issues and answer all four
questions.

![topology](img/img-008-008.png)\ 

a. OSPF neighbor adjacency is not formed between R3 in the main office and R5
in the Branch2 office. What is causing the problem?

a. There is an area ID mismatch.
b. There is a PPP authentication issue; a password mismatch.
c. There is an OSPF hello and dead interval mismatch.
d. There is a missing network command in the OSPF process on R5.

Continue checking their connected interfaces with the “show running-config” command:

R3#show running-config
\<\<output omitted\>\>
!
interface Serial1/1
 description \*\*Connected to R5-Branch2 office\*\*
 ip address 10.10.240.5 255.255.255.252
 encapsulation ppp
 ip ospf hello-interval 50
 ip ospf 3 area 0
!
\<\<output omitted\>\>

R5#show running-config
\<\<output omitted\>\>
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.6 255.255.255.252encapsulation ppp
 ip ospf 5 area 0
!
\<\<output omitted\>\>

Answer: C

Section: (none)

Explanation:
Here are the relevant parts of the router configs:

```cisco
R1
!
interface Loopback0
 description \*\*\*Loopback\*\*\*
 ip address 192.168.1.1 255.255.255.255
 ip ospf 1 area 0
!
interface Ethernet0/0
 description \*\*Connected to R1-LAN\*\*
 ip address 10.10.110.1 255.255.255.0
 ip ospf 1 area 0
!
interface Ethernet0/1
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.1 255.255.255.0
 ip ospf hello-interval 25
 ip ospf 1 area 0
!
router ospf 1
 log-adjacency-changes
!
end

R2
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.2.2 255.255.255.255
 ip ospf 2 area 0
!
interface Ethernet0/0
 description \*\*Connected to R2-LAN\*\*
 ip address 10.10.120.1 255.255.255.0
 ip ospf 2 area 0
!
interface Ethernet0/1
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.2 255.255.255.0
 ip ospf 2 area 0
!
router ospf 2logadjacency-changes
!
end


R3
!
username R6 password CISCO36
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.3.3 255.255.255.255
 ip ospf 3 area 0
!
interface Ethernet0/0
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.3 255.255.255.0
 ip ospf 3 area 0
!
interface Serial1/0
 description \*\*Connected to R4-Branch1 office\*\*
 ip address 10.10.240.1 255.255.255.252
 encapsulation ppp
 ip ospf 3 area 0
!
interface Serial1/1
 description \*\*Connected to R5-Branch2 office\*\*
 ip address 10.10.240.5 255.255.255.252
 encapsulation ppp
 ip ospf hello-interval 50
 ip ospf 3 area 0
!
interface Serial1/2
 description \*\*Connected to R6Branch3 office\*\*
 ip address 10.10.240.9 255.255.255.252
 encapsulation ppp
 ip ospf 3 area 0
 ppp authentication chap
!
router
 ospf 3router-id 192.168.3.3
!
end


R4
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.4.4 255.255.255.255
 ip ospf 4 area 2
!
interface Ethernet0/0
 ip address 172.16.113.1 255.255.255.0
 ip ospf 4 area 2
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.2 255.255.255.252
 encapsulation ppp
 ip ospf 4 area 2
!
router ospf 4
 log-adjacencychanges
!
end

R5
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.5.5 255.255.255.255
 ip ospf 5 area 0
!
interface Ethernet0/0
 ip address 172.16.114.1 255.255.255.0
 ip ospf 5 area 0
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.6 255.255.255.252
 encapsulation ppp
 ip ospf 5 area 0
!
router ospf 5
 log-adjacencychanges
!
end

R6
username R3 password CISCO36
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.6.6 255.255.255.255
 ip ospf 6 area 0
!
interface Ethernet0/0
 ip address 172.16.115.1 255.255.255.0
 ip ospf 6 area 0
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.10 255.255.255.252
 encapsulation ppp
 ip ospf 6 area 0
 ppp authentication chap
!
router ospf 6
 router-id 192.168.3.3
!
end


Continue checking their connected interfaces with the “show running-config” command:

R3#show running-config
\<\<output omitted\>\>
!
interface Serial1/1
 description \*\*Connected to R5-Branch2 office\*\*
 ip address 10.10.240.5 255.255.255.252
 encapsulation ppp
 ip ospf hello-interval 50
 ip ospf 3 area 0
!
\<\<output omitted\>\>

R5#show running-config
\<\<output omitted\>\>
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.6 255.255.255.252encapsulation ppp
 ip ospf 5 area 0
!
\<\<output omitted\>\>
```

The only difference we can see here is the line 'ip ospf hello-interval 50' on
R3. This command sets the number of seconds R3 waits before sending the next
hello packet out this interface. In this case after configuring this command,
R3 will send hello packets to R5 every 50 seconds. But the default value of
hello-interval is 10 seconds and R5 is using it. Therefore we can think of a
hello interval mismatch problem here. You can verify with the “show ip ospf
interface <interface>” command on each router.

```cisco
R3#sh ip ospf int s1/1
Serial1/1 is up, line protocol is up
Internet Address 10.10.240.5/30, Area 0
Process ID 3, Router ID 192.168.3.3, Network Type POINT_TO_POINT, Cost: 64
Enabled by interface config, including secondary ip addresses
Transmit Delay is 1 sec, State POINT_TO_POINT,Timer intervals configured, Hello 50, Dead 200, Wait 200, Retransmit 5
oob-resync timeout 200
Hello due in 00:00:28
Supports Link-local Signaling (LLS)Index 2/2, flood queue length 0
Next 0×0(0)/0×0(0)
Last flood scan length is 0, maximum is 0
Last flood scan time is 0 msec, maximum is 0 msec
Neighbor Count is 0, Adjacent neighbor count is 0
Suppress hello for 0 neighbor(s)

R5#sh ip ospf int s1/0
Serial1/0 is up, line protocol is up
Internet Address 10.10.240.6/30, Area 0
Process ID 5, Router ID 10.10.240.6, Network Type POINT_TO_POINT, Cost: 64
Enabled by interface config, including secondary ip addresses
Transmit Delay is 1 sec, State POINT_TO_POINT,Timer intervals configured, Hello 10, Dead 40, Wait 40, Retransmit 5
oob-resync timeout 40
Hello due in 00:00:04
Supports Link-local Signaling (LLS)Index 1/1, flood queue length 0
Next 0×0(0)/0×0(0)
Last flood scan length is 0, maximum is 0
Last flood scan time is 0 msec, maximum is 0 msec
Neighbor Count is 0, Adjacent neighbor count is 0
Suppress hello for 0 neighbor(s)
```

So we can see both hello and dead interval are mismatched because the dead
interval always four times the value of hello interval, unless you manually
configure the dead interval (with the ip ospf dead-interval <seconds> command).

# Q6
Refer to the topology. Your company has decided to connect the main office with
three other remote branch offices using point-to-point serial links. You are
required to troubleshoot and resolve OSPF neighbor adjacency issues between the
main office and the routers located in the remote branch offices. Use
appropriate show commands to troubleshoot the issues and answer all four
questions.

![topology](img/img-013-016.png)\ 

R1 does not form an OSPF neighbor adjacency with R2. Which option would fix the
issue?

a. R1 ethernet0/1 is shutdown. Configure no shutdown command.
b. R1 ethernet0/1 configured with a non-default OSPF hello interval of 25; configure no ip ospf hello-interval 25
c. R2 ethernet0/1 and R3 ethernet0/0 are configured with a non-default OSPF hello interval of 25; configure no ip ospf hellointerval 25
d. Enable OSPF for R1 ethernet0/1; configure ip ospf 1 area 0 command under ethernet0/1.


Continue checking their connected interfaces with the “show running-config”
command:

R1#show running-config
\<\<output omitted\>\>
!
interface Ethernet0/1
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.1 255.255.255.0
 ip ospf hello-interval 25
 ip ospf 1 area 0
!
\<\<output omitted\>\>

R2#show running-config
\<\<output omitted\>\>
!
interface Ethernet0/1
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.2 255.255.255.0
 ip ospf 2 area 0
!
\<\<output omitted\>\>

Answer: B
Section: (none)
Explanation:
Here are the relevant parts of the router configs:

R1
!
interface Loopback0
 description \*\*\*Loopback\*\*\*
 ip address 192.168.1.1 255.255.255.255
 ip ospf 1 area 0
!
interface Ethernet0/0
 description \*\*Connected to R1-LAN\*\*
 ip address 10.10.110.1 255.255.255.0
 ip ospf 1 area 0
!
interface Ethernet0/1
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.1 255.255.255.0
 ip ospf hello-interval 25
 ip ospf 1 area 0
!
router ospf 1
 log-adjacency-changes
!
end

R2
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.2.2 255.255.255.255
 ip ospf 2 area 0
!
interface Ethernet0/0
 description \*\*Connected to R2-LAN\*\*
 ip address 10.10.120.1 255.255.255.0
 ip ospf 2 area 0
!
interface Ethernet0/1
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.2 255.255.255.0
 ip ospf 2 area 0
!
router ospf 2
 logadjacency-changes
!
end

R3
username R6 password CISCO36
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.3.3 255.255.255.255
 ip ospf 3 area 0
!
interface Ethernet0/0
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.3 255.255.255.0
 ip ospf 3 area 0
!
interface Serial1/0
 description \*\*Connected to R4-Branch1 office\*\*
 ip address 10.10.240.1 255.255.255.252
 encapsulation ppp
 ip ospf 3 area 0
!
interface Serial1/1
 description \*\*Connected to R5-Branch2 office\*\*
 ip address 10.10.240.5 255.255.255.252
 encapsulation ppp
 ip ospf hello-interval 50
 ip ospf 3 area 0
!
interface Serial1/2
 description \*\*Connected to R6Branch3 office\*\*
 ip address 10.10.240.9 255.255.255.252
 encapsulation ppp
 ip ospf 3 area 0
 ppp authentication chap
!
router ospf 3
 router-id 192.168.3.3
!
end

R4
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.4.4 255.255.255.255
 ip ospf 4 area 2
!
interface Ethernet0/0
 ip address 172.16.113.1 255.255.255.0
 ip ospf 4 area 2
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.2 255.255.255.252encapsulation ppp
 ip ospf 4 area 2
!
router ospf 4
 log-adjacencychanges
!
end

R5
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.5.5 255.255.255.255
 ip ospf 5 area 0
!
interface Ethernet0/0
 ip address 172.16.114.1 255.255.255.0
 ip ospf 5 area 0
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.6 255.255.255.252
 encapsulation ppp
 ip ospf 5 area 0
!
router ospf 5
 log-adjacencychanges
!
end

R6
username R3 password CISCO36
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.6.6 255.255.255.255
 ip ospf 6 area 0
!
interface Ethernet0/0
 ip address 172.16.115.1 255.255.255.0
 ip ospf 6 area 0
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.10 255.255.255.252
 encapsulation ppp
 ip ospf 6 area 0
 ppp authentication chap
!
router ospf 6
 router-id 192.168.3.3
!
end


Continue checking their connected interfaces with the “show running-config” command:

R1#show running-config
\<\<output omitted\>\>
!
interface Ethernet0/1
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.1 255.255.255.0
 ip ospf hello-interval 25
 ip ospf 1 area 0
!
\<\<output omitted\>\>

R2#show running-config
\<\<output omitted\>\>
!
interface Ethernet0/1
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.2 255.255.255.0
 ip ospf 2 area 0
!
\<\<output omitted\>\>

We see the hello interval on R1 is not the same as R2 (and you can verify with
the “show ip ospf interface <interface> command”) -> There is a hello and dead
interval mismatch problem. We should configure “no ip ospf hello-interval 25"
on R1. Note: Maybe there are some versions of this question in the exam. For
example there are some reports saying that Ethernet0/1 on R1 is shutdown (and
this is the correct choice in the exam). So please be careful checking the
config on the routers before choosing the correct answers.

# Q7
Refer to the topology. Your company has decided to connect the main office with
three other remote branch offices using point-to-point serial links. You are
required to troubleshoot and resolve OSPF neighbor adjacency issues between the
main office and the routers located in the remote branch offices. Use
appropriate show commands to troubleshoot the issues and answer all four
questions. Instructions

![topology](img/img-018-024.png)\ 

a. OSPF neighbor adjacency is not formed between R3 in the main office and R6
in the Branch3 office. What is causing the problem?

a. There is an area ID mismatch.
b. There is a PPP authentication issue; the username is not configured on R3 and R6.
c. There is an OSPF hello and dead interval mismatch.
d. The R3 router ID is configured on R6.


R3#show running-config
\<\<output omitted\>\>
!
username R6 password CISCO36
!
interface Serial1/2
description \*\*Connected to R6-Branch3 office\*\*
 ip address 10.10.240.9 255.255.255.252
 encapsulation ppp
 ip ospf 3 area 0
 ppp authentication chap
!
\<\<output omitted\>\>
!
router ospf 3
 router-id 192.168.3.3
!
\<\<output omitted\>\>

R6#show running-config
!
\<\<output omitted\>\>
username R3 password CISCO36
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.10 255.255.255.252
 encapsulation ppp
 ip ospf 6 area 0
 ppp authentication chap
!
\<\<output omitted\>\>
!
router ospf 6
 router-id 192.168.3.3
!
\<\<output omitted\>\>

Answer: D
Section: (none)
Explanation:
Here are the relevant parts of the router configs:

R1
!
interface Loopback0
 description \*\*\*Loopback\*\*\*
 ip address 192.168.1.1 255.255.255.255
 ip ospf 1 area 0
!
interface Ethernet0/0
 description \*\*Connected to R1-LAN\*\*
 ip address 10.10.110.1 255.255.255.0
 ip ospf 1 area 0
!
interface Ethernet0/1
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.1 255.255.255.0
 ip ospf hello-interval 25
 ip ospf 1 area 0
!
router ospf 1
 log-adjacency-changes
!
end

R2
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.2.2 255.255.255.255
 ip ospf 2 area 0
!
interface Ethernet0/0
 description \*\*Connected to R2-LAN\*\*
 ip address 10.10.120.1 255.255.255.0
 ip ospf 2 area 0
!
interface Ethernet0/1
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.2 255.255.255.0
 ip ospf 2 area 0
!
router ospf 2
 logadjacency-changes
!
end

R3
username R6 password CISCO36
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.3.3 255.255.255.255
 ip ospf 3 area 0
!
interface Ethernet0/0
 description \*\*Connected to L2SW\*\*
 ip address 10.10.230.3 255.255.255.0
 ip ospf 3 area 0
!
interface Serial1/0
 description \*\*Connected to R4-Branch1 office\*\*
 ip address 10.10.240.1 255.255.255.252
 encapsulation ppp
 ip ospf 3 area 0
!
interface Serial1/1
 description \*\*Connected to R5-Branch2 office\*\*
 ip address 10.10.240.5 255.255.255.252
 encapsulation ppp
 ip ospf hello-interval 50
 ip ospf 3 area 0
!
interface Serial1/2
 description \*\*Connected to R6Branch3 office\*\*
 ip address 10.10.240.9 255.255.255.252
 encapsulation ppp
 ip ospf 3 area 0
 ppp authentication chap
!
router ospf 3
 router-id 192.168.3.3
!
end

R4
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.4.4 255.255.255.255
 ip ospf 4 area 2
!
interface Ethernet0/0
 ip address 172.16.113.1 255.255.255.0
 ip ospf 4 area 2
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.2 255.255.255.252
 encapsulation ppp
 ip ospf 4 area 2
!
router ospf 4
 log-adjacency-changes
!
end

R5
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.5.5 255.255.255.255
 ip ospf 5 area 0
!
interface Ethernet0/0
 ip address 172.16.114.1 255.255.255.0
 ip ospf 5 area 0
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.6 255.255.255.252
 encapsulation ppp
 ip ospf 5 area 0
!
router ospf 5
 log-adjacencychanges
!
end

R6
username R3 password CISCO36
!
interface Loopback0
 description \*\*Loopback\*\*
 ip address 192.168.6.6 255.255.255.255
 ip ospf 6 area 0
!
interface Ethernet0/0
 ip address 172.16.115.1 255.255.255.0
 ip ospf 6 area 0
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.10 255.255.255.252
 encapsulation ppp
 ip ospf 6 area 0
 ppp authentication chap
!
router ospf 6
 router-id 192.168.3.3!
!
end


R3#show running-config
\<\<output omitted\>\>
username R6 password CISCO36
!
interface Serial1/2
description \*\*Connected to R6-Branch3 office\*\*
 ip address 10.10.240.9 255.255.255.252
 encapsulation ppp
 ip ospf 3 area 0
 ppp authentication chap
!
\<\<output omitted\>\>
!
router ospf 3
 router-id 192.168.3.3
!
\<\<output omitted\>\>

R6#show running-config
\<\<output omitted\>\>
username R3 password CISCO36
!
interface Serial1/0
 description \*\*Connected to R3-Main Branch office\*\*
 ip address 10.10.240.10 255.255.255.252
 encapsulation ppp
 ip ospf 6 area 0
 ppp authentication chap
!
\<\<output omitted\>\>
!
router ospf 6
 router-id 192.168.3.3
!
\<\<output omitted\>\>

We are not sure about the configuration of ppp authentication in this case.
Some reports said that only one router has the “ppp authentication chap”
command but it is just a trick and is not the problem here. The real problem
here is R6 uses the same router-id of R3 (192.168.3.3) so OSPF neighborship
cannot be established. In real life, such configuration error will be shown in
the command line interface (CLI). So please check carefully for this question.

# Q8
What are three advantages of VLANs? (Choose three.)

a. They establish broadcast domains in switched networks.
b. They provide a low-latency internetworking alternative to routed networks.
c. They utilize packet filtering to enhance network security.
d. They can simplify adding, moving, or changing hosts on the network.
e. They allow access to network services based on department, not physical location.
f. They provide a method of conserving IP addresses in large networks.

Answer: ADE
Section: (none)
Explanation:

# Q9
Which command can you enter to determine whether serial interface 0/2/0 has
been configured using HDLC encapsulation?

a. router#show platform
b. router#show interfaces Serial 0/2/0
c. router#show ip interface s0/2/0
d. router#show ip interface brief

Answer: B
Section: (none)
Explanation:

# Q10
Which function of the IP SLAs ICMP jitter operation can you use to determine
whether a VoIP issue is caused by excessive end-to-end time?

a. packet loss
b. jitter
c. successive packet loss
d. round-trip time latency

Answer: D
Section: (none)
Explanation:

# Q11
Refer to the exhibit.

![exhibit](img/img-024-032.png)\ 

Which of these statements correctly describes the state of the switch once the
boot process has been completed?

a. The switch will need a different IOS code in order to support VLANs and STР.
b. Remote access management of this switch will not be possible without configuration change.
c. As FastEthernet0/12 will be the last to come up, it will be blocked by STP.
d. More VLANs will need to be created for this switch.

Answer: B
Section: (none)
Explanation:

# Q12
Refer to the exhibit.

![exhibit](img/img-025-033.png)\ 

The network administrator normally establishes a Telnet session with the switch
from host A. However, host A is unavailable. The administrator's attempt to
telnet to the switch from host В fails, but pings to the other two hosts are
successful. What is the issue?

a. The switch interfaces need the appropriate IP addresses assigned.
b. Host В and the switch need to be in the same subnet.
c. The switch needs an appropriate default gateway assigned.
d. The switch interface connected to the router is down.
e. Host В needs to be assigned an IP address in VLAN 1.

Answer: C
Section: (none)
Explanation:

# Q13
Which condition does the err-disabled status indicate on an Ethernet interface?

a. There is a duplex mismatch.
b. The device at the other end of the connection is powered off.
c. The serial interface is disabled.
d. The interface is configured with the shutdown command.
e. Port security has disabled the interface.
f. The interface is fully functioning.

Answer: E
Section: (none)
Explanation:

# Q14
Which statement about RADIUS security is true?

a. It supports EAP authentication for connecting to wireless networks.
b. It provides encrypted multiprotocol support.
c. Device-administration packets are encrypted in their entirety.
d. It ensures that user activity is fully anonymous.

Answer: A
Section: (none)
Explanation:

# Q15
a.router has learned three possible routes that could be used to reach a
destination network. One route is from EIGRP and has a composite metric of
20514560. Another route is from OSPF with a metric of 782. The last is from
RIPv2 and has a metric of 4. Which route or routes will the router install in
the routing table?

a. the RIPv2 route
b. all three routes
c. the OSPF and RIPv2 routes
d. the OSPF route
e. the EIGRP route

Answer: E
Section: (none)
Explanation:
EIGRP has the lowest administrative distance of the three.

# Q16
Which two correctly describe steps in the OSI data encapsulation process?
(Choose two.)

a. The presentation layer translates bits into voltages for transmission across the physical link.
b. The data link layer adds physical source and destination addresses and an FCS to the segment.
c. Packets are created when the network layer adds Layer 3 addresses and control information to a segment.
d. Packets are created when the network layer encapsulates a frame with source and destination host addresses and
   protocol-related control information.
e. The transport layer divides a data stream into segments and may add reliability and flow control information.

Answer: CE
Section: (none)
Explanation:

# Q17
Which two statements about IPv4 multicast traffic are true? (Choose two.)

a. It burdens the source host without affecting remote hosts.
b. It uses a minimum amount of network bandwidth.
c. It is bandwidth-intensive.
d. It simultaneously delivers multiple streams of data.
e. It is the most efficient way to deliver data to multiple receivers.

Answer: DE
Section: (none)
Explanation:

# Q18
Refer to the exhibit.

![exhibit](img/img-027-034.png)\ 

a.l of the routers in the network are configured with the ip subnet-zero
command. Which network addresses should be used for Link A and Network A?
(Choose two.)

a. Link A – 172.16.3.0/30
b. Link A – 172.16.3.112/30
c. Network A – 172.16.3.48/26
d. Network A – 172.16.3.128/25
e. Link A – 172.16.3.40/30
f. Network A – 172.16.3.192/26

Answer: AD
Section: (none)
Explanation:

# Q19
Which type of device can be replaced by the use of subinterfaces for VLAN
routing?

a. Layer 2 bridge
b. Layer 2 switch
c. Layer 3 switch
d. router

Answer: C
Section: (none)
Explanation:

# Q20
Which Layer 2 protocol encapsulation type supports synchronous and asynchronous
circuits and has built-in security mechanisms? 

a. X.25
b. HDLC
c. PPP
d. Frame Relay

Answer: C
Section: (none)
Explanation:

# Q21
Which statement about LLDP is true?

a. It is a Cisco proprietary protocol.
b. It is configured in global configuration mode.
c. The LLDP update frequency is a fixed value.
d. It runs over the transport layer.

Answer: B
Section: (none)
Explanation:

# Q22
What are two benefits of private IPv4 IP addresses? (Choose two.)

a. They are routed the same as public IP addresses.
b. They are less costly than public IP addresses.
c. They can be assigned to devices without Internet connections.
d. They eliminate the necessity for NAT policies.
e. They eliminate duplicate IP conflicts.

Answer: BC
Section: (none)
Explanation:

# Q23
If the primary root bridge experiences a power loss, which switch takes over?

a. switch 0040.0ВС0.90C5
b. switch 00E0.F90B.6BE3
c. switch 0004.9A1A.C182
d. switch 00E0.F726.3DC6

Answer: C
Section: (none)
Explanation:

# Q24
a.network administrator is troubleshooting an EIGRP problem on a router and needs to confirm the IP addresses of the
devices with which the router has established adjacency. The retransmit interval and the queue counts for the adjacent
routers also need to be checked. What command will display the required information?

a. Router# show ip eigrp neighbors
b. Router# show ip eigrp interfaces
c. Router# show ip eigrp adjacency
d. Router# show ip eigrp topology

Answer: A
Section: (none)
Explanation:

# Q25
What is the authoritative source for an address lookup?

a. a recursive DNS search
b. the operating system cache
c. the ISP local cache
d. the browser cache

Answer: A
Section: (none)
Explanation:

# Q26
Which command can you enter to verify that a BGP connection to a remote device
is established?

a. show ip bgp summary
b. show ip community-list
c. show ip bgp paths
d. show ip route

Answer: A
Section: (none)
Explanation:

# Q27
Refer to the exhibit.

![exhibit](img/img-030-035.png)\ 

The two connected ports on the switch are not turning orange or green. Which
three would be the most effective steps to troubleshoot this physical layer
problem? (Choose three.)

a. Ensure the switch has power.
b. Reseat all cables.
c. Ensure cable A is plugged into a trunk port.
d. Ensure that the Ethernet encapsulations match on the interconnected router and switch ports.
e. Reboot all of the devices.
f. Ensure that cables A and В are straight-through cables.

Answer: ABF
Section: (none)
Explanation:

# Q28
During which phase of PPPoE is PPP authentication performed?

a. the PPP Session phase
b. Phase 2
c. the Active Discovery phase
d. the Authentication phase
e. Phase 1

Answer: A
Section: (none)
Explanation:

# Q29
Which three circumstances can cause a GRE tunnel to be in an up/down state?
(Choose three.)

a. The tunnel interface IP address is misconfigured.
b. The tunnel interface is down.
c. A valid route to the destination address is missing from the routing table.
d. The tunnel address is routed through the tunnel itself.
e. The ISP is blocking the traffic.
f. An ACL is blocking the outbound traffic.

Answer: BCD
Section: (none)
Explanation:

# Q30
Which three statements about IPv6 prefixes are true? (Choose three.)

a. FEC0::/10 is used for IPv6 broadcast.
b. FC00::/7 is used in private networks.
c. FE80::/8 is used for link-local unicast.
d. FE80::/10 is used for link-local unicast.
e. 2001::1/127 is used for loopback addresses.
f. FF00::/8 is used for IPv6 multicast.

Answer: BDF
Section: (none)
Explanation:

# Q31
Which command can you enter to display duplicate IP addresses that the DHCP
server assigns?

a. show ip dhcp conflict 10.0.2.12
b. show ip dhcp database 10.0.2.12
c. show ip dhcp server statistics
d. show ip dhcp binding 10.0.2.12

Answer: A
Section: (none)
Explanation:

# Q32
Refer to the exhibit.

![exhibit](img/img-032-036.png)\ 

Which three ports will be STP designated ports if all the links are operating
at the same bandwidth? (Choose three.)

a. Switch B - Fа0/0
b. Switch A - Fa0/1
c. Switch В - Fa0/l
d. Switch С - Fа0/1
e. Switch A - Fa0/0
f. Switch С - Fa0/0

Answer: ABC
Section: (none)
Explanation:

# Q33
Which two statements about using leased lines for your WAN infrastructure are
true? (Choose two.)

a. Leased lines provide inexpensive WAN access.
b. Leased lines with sufficient bandwidth can avoid latency between endpoints.
c. Leased lines require little installation and maintenance expertise.
d. Leased lines provide highly flexible bandwidth scaling.
e. Multiple leased lines can share a router interface.
f. Leased lines support up to T1 link speeds.

Answer: CD
Section: (none)
Explanation:

# Q34
Refer to the exhibit.

![exhibit](img/img-033-037.png)\ 

The network administrator cannot connect to Switch 1 over a Telnet session,
although the hosts attached to Switch1 can ping the interface Fa0/0 of the
router. Given the information in the graphic and assuming that the router and
Switch2 are configured properly, which of the following commands should be
issued on Switch1 to correct this problem?

a. Switch1(config)# ip default-gateway 192.168.24.1
b. Switch1(config)# interface fa0/1Switch1(config-if)# switchport mode trunk
c. Switch1(config)# line con0Switch1(config-line)# password ciscoSwitch1(config-line)# login
d. Switch1(config)# interface fa0/1Switch1(config-if)# ip address 192.168.24.3 255.255.255.0
e. Switch1(config)# interface fa0/1Switch1(config-if)# duplex fullSwitch1(confiq-if)# speed 100

Answer: A
Section: (none)
Explanation:

# Q35
Which two statements about IPv6 and routing protocols are true? (Choose two.)

a. EIGRPv3 was developed to support IPv6 routing.
b. OSPFv3 was developed to support IPv6 routing.
c. Loopback addresses are used to form routing adjacencies.
d. EIGRP, OSPF, and BGP are the only routing protocols that support IPv6.
e. Link-local addresses are used to form routing adjacencies.

Answer: BE
Section: (none)
Explanation:

# Q36
Refer to the exhibit.

![exhibit](img/img-034-038.png)\ 

Each of these four switches has been configured with a hostname, as well as
being configured to run RSTP. No other configuration changes have been made.
Which three of these show the correct RSTP port roles for the indicated
switches and interfaces? (Choose three.)

a. SwitchD. Gi0/2, root
b. SwitchA, Fa0/2, designated
c. SwitchB, Gi0/l, designated
d. SwitchA, Fa0/l, root
e. SwitchB, Gi0/2, root
f. SwitchC, Fa0/2, root

Answer: ABD
Section: (none)

Explanation:

# Q37
Which feature builds a FIB and an adjacency table to expedite packet
forwarding?

a. cut through
b. fast switching
c. process switching
d. Cisco Express Forwarding

Answer: D
Section: (none)
Explanation:

# Q38
Which command can you enter to verify that a 128-bit address is live and
responding?

a. traceroute
b. telnet
c. ping
d. ping ipv6

Answer: D
Section: (none)
Explanation:

# Q39
What will happen if a private IP address is assigned to a public interface
connected to an ISP?

a. A conflict of IP addresses happens, because other public routers can use the same range.
b. Addresses in a private range will not be routed on the Internet backbone.
c. Only the ISP router will have the capability to access the public network.
d. The NAT process will be used to translate this address to a valid IP address.

Answer: B
Section: (none)
Explanation:

# Q40
DRAG DROP

![drag_n_drop](img/img-036-039.png)\ 

PC_1 is sending packets to the FTP server. Consider the packets as they leave
RouterA interface Fa0/0 towards RouterB. Drag the correct frame and packet
address to their place in the table.

a. You cannot drag and drop here
b. So just choose answer A
c. Try to workout the drag/drop in your head
d. Afterwards, checkout the explanation

Answer:
Section: (none)
Explanation:
a. a packet travels the network, its src/dst IP addresses donot change. The
MAC addresses of the Layer2 frame however, are adjusted to reflect the src/dst
MAC's of sender/receiver on each L2 traversal.

![drag_n_drop](img/img-037-040.png)\ 


# Q41
What are two reasons that duplex mismatches can be difficult to diagnose?
(Choose two.)

a. The interface displays a connected (up/up) state even when the duplex settings are mismatched.
b. 1-Gbps interfaces are full-duplex by default.
c. Full-duplex interfaces use CSMA/CD logic, so mismatches may be disguised by collisions.
d. The symptoms of a duplex mismatch may be intermittent.
e. Autonegotiation is disabled.

Answer: AD
Section: (none)
Explanation:

# Q42
Which condition indicates that service password-encryption is enabled?

a. The local username password is in clear text in the configuration.
b. The enable secret is in clear text in the configuration.
c. The local username password is encrypted in the configuration.
d. The enable secret is encrypted in the configuration.

Answer: C
Section: (none)
Explanation:

# Q43
Which command would you configure globally on a Cisco router that would allow
you to view directly connected Cisco devices?

a. cdp run
b. enable cdp
c. cdp enable
d. run cdp

Answer: A
Section: (none)
Explanation:


