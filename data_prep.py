import openpyxl
import os
import glob2
import pandas as pd
import datetime as dt

def read_in(input_folder):
    """_summary_

    Args:
        input_folder (_type_): _description_

    Returns:
        _type_: _description_
    """
    regex = os.path.join(input_folder, "*.csv")
    csv_path_list = [el for el in glob2.glob(regex) if "out" not in el ] 

    df_list = [pd.read_csv(csv) for csv in csv_path_list]
    df = pd.concat(df_list, axis=0)
    return df

if __name__ == '__main__':

    input_folder = "/Users/assansanogo/Downloads/dashboard/refactor/refactor/src/powerbi"

    print("reading the data in")
    df = read_in(input_folder)

    df_lite= df[df["Marque_corrected"]!="OTHER"].copy()

    # arbitrary time and day
    df_lite["day"]=1
    df_lite["hour"]=1

    #dataset that stores products-brands
    df_products=df_lite[["Marque_corrected","Code_Produit", "Designation"]].drop_duplicates()

    print("reading the growth in")
    growth = 5/100
    
    # add date from month and year column
    df_lite["date"]=pd.to_datetime(dict(year= df_lite.year, 
                                        month= df_lite.month, 
                                        day= df_lite.day))



    print("dataset with date column")
    print(df_lite.head())

    # sort data by code produit , designation and date
    df_lite_sorted = df_lite.sort_values(by=['Code_Produit', 'Designation','date'], ascending=True)

    # ordered dataset
    print("dataset ordered")
    print(df_lite_sorted.head())

    # summarized metrics (at this stage we should not have duplicates)
    print("dataset summarized by month")
    df_lite_sorted_grouped = df_lite_sorted.groupby(["Code_Produit","Designation","date"]).agg({'CA_Brut_TTC_corrected':'sum',"Qte_corrected":'sum' })
    

    df_dates = pd.DataFrame(pd.date_range(start='1/1/2022', end='01/01/2024', freq="MS"))
    df_dates.columns=["date"]
    all_products = df_lite_sorted_grouped.reset_index()[["Code_Produit","Designation"]].drop_duplicates()
    
    # cross product dates and products-designation
    dummy = df_dates.merge(all_products, how='cross')
    print("DUMMY")
    print(dummy.sort_values(by=["Code_Produit","Designation"]).head())
    

    # merge with dataset to get date/months with no sales
    merged = pd.merge(df_lite_sorted_grouped,dummy, on=["Code_Produit","Designation","date"], how="outer")
    
    
    merged = merged.sort_values(by=["Code_Produit","Designation","date"])
    
    merged["year"]= merged["date"].apply(lambda x: x.year)
    merged["month"]= merged["date"].apply(lambda x: x.month)
    merged["d"]= merged["date"].apply(lambda x: x.day)
    merged["h"]= 1
    
    # datetime index cration
    merged["fdate"]=pd.to_datetime(dict(year= merged.year,
                                        month= merged.month, 
                                        day= merged.d,
                                        hour=merged.h))
    
    
    merged.set_index(['fdate'], inplace=True)
    print(merged.head())

    #merged.to_csv(os.path.join(input_folder,"out.csv"))
    #raise
    print(merged.head())

    # shift by 12 periods/rows (= 1year) to get the objective value
    print("columns with metric by a year")
    #print(merged.groupby(["Code_Produit","Designation"])["CA_Brut_TTC_corrected"].shift(11))
    
    merged["CA_objective"] = merged.groupby(["Code_Produit","Designation"])["CA_Brut_TTC_corrected"].shift(12)*(1+growth)
    
    merged["Qte_objective"] = merged.groupby(["Code_Produit","Designation"])["Qte_corrected"].shift(12)*(1+growth)
    
    # output the file to excel
    print("saving file to excel/csv")
    columns = ["date","Code_Produit","Designation","CA_Brut_TTC_corrected","Qte_corrected","CA_objective","Qte_objective","year","month"]
    # retrieving brand information
    out = pd.merge(merged[columns],df_products,on=["Code_Produit", "Designation"], how='left')
    out.to_csv(os.path.join(input_folder,"out.csv"))

