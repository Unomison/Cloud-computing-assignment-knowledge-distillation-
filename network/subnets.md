# Task 5: Subnetting and Network Access Control (NACL)

## 1. Subnet Allocation

Address Block: `10.20.0.0/16`

Allocation Strategy: Allocate from largest host requirement to smallest, starting at `10.20.0.0`, contiguous placement, smallest prefix length satisfying usable hosts $\ge \text{required hosts}$.

Formula:
$$\text{Usable Hosts} = 2^{32 - \text{prefix}} - 2$$

### Step-by-Step Allocation:

1. **`app` subnet (1,000 hosts required):**
   - $2^9 - 2 = 510 < 1000$ (insufficient)
   - $2^{10} - 2 = 1022 \ge 1000$ $\implies$ 10 host bits $\implies$ Prefix length $= 32 - 10 = /22$
   - Network address: `10.20.0.0/22`
   - Subnet Mask: `255.255.252.0`
   - Usable Host Range: `10.20.0.1` – `10.20.3.254`
   - Broadcast Address: `10.20.3.255`
   - Number of Usable Hosts: $1,022$
   - Next available address: `10.20.4.0`

2. **`public` subnet (250 hosts required):**
   - $2^7 - 2 = 126 < 250$ (insufficient)
   - $2^8 - 2 = 254 \ge 250$ $\implies$ 8 host bits $\implies$ Prefix length $= 32 - 8 = /24$
   - Network address: `10.20.4.0/24`
   - Subnet Mask: `255.255.255.0`
   - Usable Host Range: `10.20.4.1` – `10.20.4.254`
   - Broadcast Address: `10.20.4.255`
   - Number of Usable Hosts: $254$
   - Next available address: `10.20.5.0`

3. **`data` subnet (100 hosts required):**
   - $2^6 - 2 = 62 < 100$ (insufficient)
   - $2^7 - 2 = 126 \ge 100$ $\implies$ 7 host bits $\implies$ Prefix length $= 32 - 7 = /25$
   - Network address: `10.20.5.0/25`
   - Subnet Mask: `255.255.255.128`
   - Usable Host Range: `10.20.5.1` – `10.20.5.126`
   - Broadcast Address: `10.20.5.127`
   - Number of Usable Hosts: $126$
   - Next available address: `10.20.5.128`

4. **`management` subnet (20 hosts required):**
   - $2^4 - 2 = 14 < 20$ (insufficient)
   - $2^5 - 2 = 30 \ge 20$ $\implies$ 5 host bits $\implies$ Prefix length $= 32 - 5 = /27$
   - Network address: `10.20.5.128/27`
   - Subnet Mask: `255.255.255.224`
   - Usable Host Range: `10.20.5.129` – `10.20.5.158`
   - Broadcast Address: `10.20.5.159`
   - Number of Usable Hosts: $30$

---

## 2. Subnet Summary Table

| Subnet Name | Network Address | Prefix Length | Usable Host Range | Broadcast Address | Usable Hosts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **app** | `10.20.0.0` | `/22` | `10.20.0.1` – `10.20.3.254` | `10.20.3.255` | 1,022 |
| **public** | `10.20.4.0` | `/24` | `10.4.0.1` – `10.20.4.254` | `10.20.4.255` | 254 |
| **data** | `10.20.5.0` | `/25` | `10.20.5.1` – `10.20.5.126` | `10.20.5.127` | 126 |
| **management** | `10.20.5.128` | `/27` | `10.20.5.129` – `10.20.5.158` | `10.20.5.159` | 30 |

*(Note: Total allocated address space is $1024 + 256 + 128 + 32 = 1440$ addresses out of $65536$ available in `10.20.0.0/16`).*

---

## 3. Explanations

### (a) Why a Stateless NACL Needs Separate Rules for Reply Traffic
Unlike stateful firewalls (such as Security Groups or iptables with `conntrack`), a Network Access Control List (NACL) is completely **stateless**. This means the NACL does not maintain a connection table and evaluates every single IP packet in total isolation, without knowledge of whether the packet is part of an existing, established bidirectional TCP session or an unsolicited new connection. 

Consequently:
1. When an external client sends an HTTP request to the public load balancer on inbound port 80/443, the inbound NACL rule allows it. However, the return traffic (the HTTP response) travel outbound towards the client's temporary ephemeral port (1024–65535). Because the NACL does not "remember" the incoming request, this outbound response packet is dropped by default unless there is an explicit outbound rule permitting traffic to ephemeral ports.
2. Similarly, when the load balancer proxies traffic by opening a connection to the application servers in the `app` subnet on outbound port 8000, the response packets returning from the `app` subnet to the load balancer arrive as inbound packets on the load balancer's ephemeral port. Without an explicit inbound rule allowing traffic from `10.20.0.0/22` on ephemeral ports (1024–65535), the response would be dropped and the connection would time out.

### (b) Why Rule Ordering Matters for `198.51.100.0/24`
NACLs process rules in numerical order, starting from the **lowest rule number upward**, and operate on a **first-match-wins** principle. Once a packet matches all attributes of a rule, that rule's action (`allow` or `deny`) is immediately executed, and all subsequent rules are ignored.

In this architecture, rule 100 explicitly **denies** all traffic from the abusive range `198.51.100.0/24`, while rule 200 and rule 210 **allow** inbound TCP traffic on ports 80 and 443 from `0.0.0.0/0` (anywhere). Because `198.51.100.0/24` is a subset of `0.0.0.0/0`, placing the deny rule at a lower number (100 < 200) ensures that packets originating from the abusive range are intercepted and dropped before the broader allow rule (`0.0.0.0/0`) is ever evaluated. If the deny rule had a higher rule number than 200/210 (e.g., rule 350), an abusive packet targeting port 80 or 443 would match rule 200/210 first and be permitted, rendering the security block ineffective.

