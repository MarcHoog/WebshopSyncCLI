from typing import Optional
import requests
from jinja2 import Template

from diffsync_cli.clients.perfion.models import PerfionResult
from diffsync_cli.clients.perfion.parsing import perfion_resp_to_dict

class PerfionClient:
    def __init__(self, api_url: str = "https://perfion.tricorp.com:85/Perfion/GetData.asmx"):
        self.api_url = api_url
        self.headers = {
            "Content-Type": "text/xml; charset=utf-8"
        }

    def _build_soap_envelope(self, query: str) -> str:
        return f"""<?xml version="1.0" encoding="utf-8"?>
                    <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                                    xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                    <soap12:Body>
                        <ExecuteQuery xmlns="http://perfion.com/">
                        <query><![CDATA[{query}]]></query>
                        </ExecuteQuery>
                    </soap12:Body>
                    </soap12:Envelope>
        """

    def _send_query(self, query: str) -> requests.Response:
        body = self._build_soap_envelope(query)
        response = requests.post(
            self.api_url,
            data=body,
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        return response

    @staticmethod
    def __get_products_query(index, per_page):
        template = Template("""
        <Query>
        <Select languages="NLD" index="{{ index }}" maxCount="{{ per_page }}" options="IncludeTotalCount,IncludeFeatureViewOrder">
            <Feature id="**" view="Detail"/>
        </Select>
        <From id="100"/>
        <Where>
            <Clause id="Category" operator="HAS"/>
            <Clause id="stage" operator="=" value="Approved"/>
            <Clause id="ReleaseToERP" operator="=" value="Yes"/>
            <Clause id="ItemStatus" operator="=" value="Voorraad artikel"/>
            <Clause id="ERPCompany" operator="=" value="37904"/>
        </Where>
        <Order><By id="String" direction="asc"/></Order>
        </Query>
        """)
        return template.render(index=index, per_page=per_page)


    def get_products(self, per_page=100, total_pages=1):
        if total_pages < -1 or total_pages == 0:
            raise(ValueError("Total page cannot be below -1 or 0"))

        start = 0
        results = []
        pages = 0
        status_code = -1

        while pages < total_pages or total_pages == -1:

            paging_params = {
                "index": start,
                "per_page": per_page
            }

            result  = self._send_query(self.__get_products_query(**paging_params))
            status_code = result.status_code
            text = result.content.decode("utf-8")
            data = perfion_resp_to_dict(text) # type: ignore

            results.extend(data.get("products", []))
            start += per_page

            if len(results) == data.get("totalCount"):
                break

        return PerfionResult(
            status_code=status_code,
            data=results
        )
