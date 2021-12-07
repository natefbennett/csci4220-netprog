Network Programming
Lab9

The default mss is fixed to 512 or 536, it changes only after the tcp handshake between client and server.
The client and server announce their own mss values, and the mss is then selected depending on end point's buffer and outgoing interface MTU.
108.177.112.106  
maximum segment size: 512
recieve buffer size: 4
maximum segment size: 1368
recieve buffer size: 4

128.113.0.2      
maximum segment size: 512
recieve buffer size: 4
maximum segment size: 1448
recieve buffer size: 4

127.0.0.1 
maximum segment size: 512
recieve buffer size: 4
connect: Connection refused
maximum segment size: 512
recieve buffer size: 4
Connection refused for local host, no packet received thus mss does not change.