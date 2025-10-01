from pyflink.datastream.functions import MapFunction
import json, re
from datetime import datetime
from preprocess import *

class NewsEnricher(MapFunction):
    def map(self, msg: str):
        data = json.loads(msg)
        
        writer = re.search(r"([가-힣]{2,4})\s?기자", data.get("content", ""))
        data["writer"] = writer.group(1) if writer else "연합뉴스"

        try:
            dt = datetime.strptime(data["write_date"], "%a, %d %b %Y %H:%M:%S %z")
            data["write_date"] = dt.isoformat()
        except:
            pass

        data["keywords"] = data["title"].split()[:3]

        return data


