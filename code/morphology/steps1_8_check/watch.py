import threading, os, time, faulthandler, sys
def _w():
    t0 = time.time()
    while True:
        rss = int(open(f"/proc/{os.getpid()}/status").read().split("VmRSS:")[1].split()[0]) / 1e6
        if rss > 6.5:
            print(f"RSS {rss:.2f} GB at {time.time()-t0:.0f}s; stack:", flush=True)
            faulthandler.dump_traceback(all_threads=True); os._exit(3)
        time.sleep(0.5)
threading.Thread(target=_w, daemon=True).start()
