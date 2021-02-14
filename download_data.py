import json
import os
import re
import sys
import time
from collections import Counter

from requests_html import HTMLSession

from configuration import configuration


def update_data(company_name=None):
    download_data_companies(company_name);
    data_processing();

def download_data_companies(company_name=None):
    print("[Start downloading data from companies]");
    
    if company_name != None:
        get_data_company(company_name + ".json");
    else:
        for name in os.listdir(configuration["PAGES"][0]["PATH"]):
            get_data_company(name);

    print("[End of data downloading from companies]");

def get_data_company(company_name):
    print(f"Processing {company_name}");

    data = {};

    with open(f"{configuration['PAGES'][0]['PATH']}{company_name}", encoding="utf-8") as company:
        company_data = json.load(company);

    for key, value in company_data.items():
        
        if value["URL"][:5] == "http:":
            session = HTMLSession(verify=False);
        else:
            session = HTMLSession();

        result = session.get(value["URL"]);

        if "SHOW_DATA" in value:
            script = "() => { " + value["SHOW_DATA"] + " }";
            result.html.render(script=script);
        else:
            result.html.render();

        rate = {};

        rate.update({"URL": value["URL"]});

        power = extract_data(result, value["POWER"]);
        if "POWER_OPERATION" in value and power != None:
            power = calcule_power(power, value["POWER_OPERATION"]);
        rate.update( { "POWER":  str(power).replace(".", ",") } );

        if isinstance(value["ENERGY"], list):
            electricity = [];

            for section in value["ENERGY"]:
                electricity.append(
                    str(extract_data(result, section)).replace(".", ",")
                );

            rate.update({"ENERGY": electricity});
        else:
            rate.update(
                {
                    "ENERGY": 
                    str(extract_data(result, value["ENERGY"])).replace(".", ",")
                }
            );

        rate.update({"NOTES": value["NOTES"]});
        data.update({key: rate});
        
        with open(f"{configuration['DATA_PATH']}{configuration['PAGES'][0]['NAME']}/{company_name}", "w", encoding="utf-8") as company:
            json.dump(data, company, sort_keys=True, indent=4);

def calcule_power(power, power_operation):
    number = "";
    signo = "";
    for caracter in power_operation:

        if caracter in "+-*/" or caracter == power_operation[-1]:
            if number != "":
                if caracter == power_operation[-1]:
                    number += caracter;
                    
                if signo == "+":
                    power = float(power.replace(",", ".")) + float(number);
                elif signo == "-":
                    power = float(power.replace(",", ".")) - float(number);
                elif signo == "*":
                    power = float(power.replace(",", ".")) * float(number);
                elif signo == "/":
                    power = float(power.replace(",", ".")) / float(number);

                number = "";
                power = str(power);

            signo = caracter;
        else:
            number += caracter;

    return str(power)[:8];

def extract_data(result, xpath):
    if not len(xpath) > 0:
        print(f"Empty path - {xpath}");
        return None;
    elif result.html.xpath(xpath) == []:
        print(f"No result - {xpath}");
        return None;
    else:
        return normalize(result.html.xpath(xpath));

def normalize(data):
    if isinstance(data, list):
        data = data[0];

    result = re.search("[0-9]?[0-9](,?.?)[0-9]+", data) or re.search("[0-9]", data);

    try:
        value = result[0];
        if len(value) < 8 and value != "0":
            for i in range(8 - len(value)):
                value += "0";

        return value[:8];
    except Exception as error:
        print(f"No results in {data}");
        return 0;

def data_processing():
    data = {};

    for name in os.listdir("data/energy"):
        with open(f"data/energy/{name}", "r", encoding="utf-8") as company:
            file_data = json.load(company);
            data.update( { os.path.splitext(name)[0]: file_data } );

    # Calcular potencias
    power = []

    for company, company_data in data.items():
        for rate, rate_data in company_data.items():
            power.append( { "COMPANY": company, "RATE": rate, "URL": rate_data["URL"], "POWER": rate_data["POWER"] } );
            
    power.sort(key=lambda item : item["POWER"]);

    # Grafica de potencias
    power_chart = {"labels": [], "series": []};

    for item in power:
        power_chart["labels"].append(item["POWER"][:4]);
    
    power_chart["series"] = list(dict(Counter(power_chart["labels"])).values());
    power_chart["labels"] = list(dict(Counter(power_chart["labels"])).keys());

    # Calcular electricidad
    rate1 = []
    rate2 = []
    rate3 = []

    for company, company_data in data.items():
        for rate, rate_data in company_data.items():
            if not isinstance(rate_data["ENERGY"], list):
                rate1.append( { "COMPANY": company, "RATE": rate, "URL": rate_data["URL"], "ENERGY": rate_data["ENERGY"] } );
            elif len(rate_data["ENERGY"]) == 2:
                rate2.append( { "COMPANY": company, "RATE": rate, "URL": rate_data["URL"], "ENERGY": rate_data["ENERGY"] } );
            elif len(rate_data["ENERGY"]) == 3:
                rate3.append( { "COMPANY": company, "RATE": rate, "URL": rate_data["URL"], "ENERGY": rate_data["ENERGY"] } );

    rate1.sort(key=lambda item : item["ENERGY"]);
    rate2.sort(key=lambda item : (item["ENERGY"][0], item["ENERGY"][1]));
    rate3.sort(key=lambda item : (item["ENERGY"][0], item["ENERGY"][1], item["ENERGY"][2]));

    # Grafica de energias
    energy_rate1_chart = {"labels": [], "series": []};

    for item in rate1:
        energy_rate1_chart["labels"].append(item["ENERGY"][:4]);
    
    energy_rate1_chart["series"] = list(dict(Counter(energy_rate1_chart["labels"])).values());
    energy_rate1_chart["labels"] = list(dict(Counter(energy_rate1_chart["labels"])).keys());

    # Grafica 2 precios
    energy_rate2_chart = [{"labels": [], "series": []}, {"labels": [], "series": []}];

    for item in rate2:
        energy_rate2_chart[0]["labels"].append(item["ENERGY"][0][:4]);
        energy_rate2_chart[1]["labels"].append(item["ENERGY"][1][:4]);

    energy_rate2_chart[0]["series"] = list(dict(Counter(energy_rate2_chart[0]["labels"])).values());
    energy_rate2_chart[0]["labels"] = list(dict(Counter(energy_rate2_chart[0]["labels"])).keys());
    energy_rate2_chart[1]["series"] = list(dict(Counter(energy_rate2_chart[1]["labels"])).values());
    energy_rate2_chart[1]["labels"] = list(dict(Counter(energy_rate2_chart[1]["labels"])).keys());

    # Grafica 3 precios
    energy_rate3_chart = [{"labels": [], "series": []}, {"labels": [], "series": []}, {"labels": [], "series": []}];

    for item in rate3:
        energy_rate3_chart[0]["labels"].append(item["ENERGY"][0][:4]);
        energy_rate3_chart[1]["labels"].append(item["ENERGY"][1][:4]);
        energy_rate3_chart[2]["labels"].append(item["ENERGY"][2][:4]);
    
    energy_rate3_chart[0]["series"] = list(dict(Counter(energy_rate3_chart[0]["labels"])).values());
    energy_rate3_chart[0]["labels"] = list(dict(Counter(energy_rate3_chart[0]["labels"])).keys());
    energy_rate3_chart[1]["series"] = list(dict(Counter(energy_rate3_chart[1]["labels"])).values());
    energy_rate3_chart[1]["labels"] = list(dict(Counter(energy_rate3_chart[1]["labels"])).keys());
    energy_rate3_chart[2]["series"] = list(dict(Counter(energy_rate3_chart[2]["labels"])).values());
    energy_rate3_chart[2]["labels"] = list(dict(Counter(energy_rate3_chart[2]["labels"])).keys());

    data = {
        "power_cheap": power[:10],
        "power_expensive": power[-10:],
        "power_chart": power_chart,
        "rate1_cheap": rate1[:10],
        "rate1_expensive": rate1[-10:],
        "energy_rate1_chart": energy_rate1_chart,
        "rate2_cheap": rate2[:10],
        "rate2_expensive": rate2[-10:],
        "energy_rate2_chart": energy_rate2_chart,
        "rate3_cheap": rate3[:10],
        "rate3_expensive": rate3[-10:],
        "energy_rate3_chart": energy_rate3_chart
    };

    with open("data/data.json", "w", encoding="utf-8") as file_data:
        json.dump(data, file_data)
    
if len(sys.argv) > 1:
    update_data(sys.argv[1]);
else:
    update_data();
