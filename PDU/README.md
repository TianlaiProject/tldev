# PDU(Power Distribution Unit) Controller

Two python codes using two protocols are provided, one is **SNMP**(**S**imple **N**etwork **M**anagement **P**rotocol; **suggested**), the other is **HTTP**(**Not** suggested).

pdu_http.py is earlier developed by Shifan Zuo;

pdu_snmp.py is then developed by Jixia Li.

Using snmp protocol is more efficient and has much faster response and so is **suggested**.

Using http protocol is **not** suggested becaused of authentication problem and slow response.

This code is used for APC PDU. Users should set up SNMP connection parameters in the PDU device before using this code.

## Usage

`python pdu_snmp.py -h`

