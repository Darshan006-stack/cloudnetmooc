# Paste this method over statsReplyHandler() inside the class in bwmon.py.
# It is NOT the full bwmon.py. It tries common names and prints what it finds,
# because I have not seen the original file.

def statsReplyHandler(self, ev):
    import time
    msg = ev.msg
    dp = msg.datapath

    # Switch name: try the file's likely lookups, else build "s<dpid>"
    switchName = None
    for attr in ('dpidToName', 'dpid2name', 'dpidToSwitch'):
        table = getattr(self, attr, None)
        if table and dp.id in table:
            switchName = table[dp.id]
            break
    if switchName is None:
        switchName = 's%d' % dp.id

    if not hasattr(self, '_prevBytes'):
        self._prevBytes = {}
        self._prevTime = {}
    now = time.time()

    ports = self.topo.ports[switchName]

    for stat in msg.body:
        port = stat.port_no
        if port not in ports.keys():        # virtual port, skip
            continue

        neighbor = ports[port]
        name = neighbor if isinstance(neighbor, str) else str(neighbor[0])
        if not name.startswith('h'):        # only host-facing ports
            continue

        key = (switchName, port)
        total = stat.rx_bytes + stat.tx_bytes
        prev = self._prevBytes.get(key, total)
        prevT = self._prevTime.get(key, now)
        self._prevBytes[key] = total
        self._prevTime[key] = now

        dt = now - prevT
        bw = (total - prev) * 8.0 / dt if dt > 0 else 0.0

        # Record bandwidth with whichever helper the file provides
        for helper in ('updateHostBW', 'updateBandwidth', 'setHostBW', 'updateHost'):
            fn = getattr(self, helper, None)
            if callable(fn):
                fn(name, bw)
                break
        else:
            print('bwmon: no update helper found; %s -> %.0f bps' % (name, bw))
