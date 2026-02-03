import pandas as pd
import yfinance as yf
import os
import numpy as np
import math
import matplotlib.pyplot as plt
import time
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import seaborn as sns
import dash
from jupyter_dash import JupyterDash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

from IPython.core.display import display, HTML
from dash import Dash, dash_table

# functions below

def create_tickers(co_dict):
    # iterates through the dictionary of companies
    for key, values in co_dict.items():
        # creates the ticker object for each company and adds to the dictionary values
        co_dict[key].append(yf.Ticker(values[0])) # now index 1 of the dictionary
    print("Tickers created")
    return(co_dict)
####

def extract_price_history(co_dict):
    
    drop_tickers = []
    
    # iterates through the dictionary of companies
    for key, values in co_dict.items():
        # creates a dataframe of stock price history for past 6months
        # appends the dataframe to the dictionary values
        #print(key)
        try: ### 6-month data
            df = values[2].history(period="6mo")
            if ('Empty Dataframe' in str(df)):
                drop_tickers.append(key)
                print('adding to drop tickers')
            else:
                co_dict[key].append(df)
                
            
            #co_dict[key].append(values[2].history(period="1mo"))
            #co_dict[key].append(values[2].history(period="5d"))
            
            ### 1-month data, if 6-month successful
            try: 
                df = values[2].history(period="1mo") 
                if ('Empty Dataframe' in str(df)):
                    drop_tickers.append(key)
                    print('adding to drop tickers')
                else:
                    co_dict[key].append(df)
                
                ### 5-day data, if 1-month and 6-month successful
                try: 
                    df = values[2].history(period="5d")
                    if ('Empty Dataframe' in str(df)):
                        drop_tickers.append(key)
                        print('adding to drop tickers')
                    else:
                        co_dict[key].append(df)
                    
                except: # 5-day failed
                    print("Could not pull data for", key)
                    drop_tickers.append(key)
                
            except: # 1-month failed
                print("Could not pull data for", key)
                drop_tickers.append(key)
            
        except: # 6-month failed
            print("Could not pull data for", key)
            drop_tickers.append(key)
            continue
    #company_tickers[key][2] = values[1].history(period="6mo").reset_index(drop = False) # if the df is already added
    
    for ticker in drop_tickers:
        del(co_dict[ticker])
        print(f'Deleted {ticker} from the dictionary')
    
    print("\n6 Month price history extracted! Thanks Yahoo Finance")
    return(co_dict)
####

def clean_price_history(co_dict):
    # keep only the date and closing value.
    # Remove columns for values for daily open, high, low, volume, dividends, and stock splits
    for key, values in co_dict.items():
        # remove unnecessary columns
        #print(key)
        if ( len(values) >= 6):
                # 5 day data
            if (values[-1].shape[0] > 0):
                values[-1] = values[-1].reset_index(drop = False)
                values[-1] = values[-1][['Date', 'Close']]
        if ( len(values) >= 5): # skips the keys that couldn't pull price data
            # 1 month data
            if (values[-2].shape[0] > 0):
                values[-2] = values[-2].reset_index(drop = False)
                values[-2] = values[-2][['Date', 'Close']]
        if ( len(values) >= 4): # skips the keys that couldn't pull price data
            # 6 month data
            if (values[-3].shape[0] > 0):
                values[-3] = values[-3].reset_index(drop = False)
                values[-3] = values[-3][['Date', 'Close']]
    print("Dataframes cleaned\n")
    return(co_dict)
####

def add_recommendations(co_dict):

    # adds the recommendation for each stock
    for key, values in co_dict.items():
        #
        try:
            values.append(values[2].info['recommendationKey'])
        except:
            values.append(np.nan)
            print("No recommendation for", key)
        #
        try:
            values.append(values[2].info['numberOfAnalystOpinions'])
        except:
            values.append(np.nan)
            print("Number of analysts is 0 for", key)
    print("\nRecommendations added to the master dictionary")
    return(co_dict)
####
def calculate_changes(co_dict):

    # create dataframe with name of stock, and column for each percentage change
    companies, change_5day, percent_5day, change_1mo, percent_1mo = [], [], [], [], []
    change_6mo, percent_6mo, prices_day, prices_1mo = [], [], [], []
    prices_6mo, recommendation, num_analysts = [], [], []

    for key, values in co_dict.items():
    
        if ( len(values) >= 8 ): # skips the keys that couldn't pull price data
            companies.append(key) ##### previously had it append the company first - 
            #print(key)
            # 5 days 
            if (values[-3].shape[0] > 0):
                first = co_dict[key][-3]['Close'][0]
                nrows = co_dict[key][-3].shape[0]
                last = co_dict[key][-3]['Close'][nrows - 1]
                
                change_5day.append(last - first)
                percent_5day.append(round((last - first) / first * 100, 2))
                prices_day.append((first, last))
            else: 
                change_5day.append(np.nan)
                percent_5day.append(np.nan)
                prices_day.append(np.nan)

            # 1 month
            if (values[-4].shape[0] > 0):
                first = co_dict[key][-4]['Close'][0]
                nrows = co_dict[key][-4].shape[0]
                last = co_dict[key][-4]['Close'][nrows - 1]

                change_1mo.append(last - first)
                percent_1mo.append(round((last - first) / first * 100, 2))
                prices_1mo.append((first, last))
                
            else: 
                change_1mo.append(np.nan)
                percent_1mo.append(np.nan)
                prices_1mo.append(np.nan)
    
            # 6 months
            if (values[-5].shape[0] > 0):
                first = co_dict[key][-5]['Close'][0]
                nrows = co_dict[key][-5].shape[0]
                last = co_dict[key][-5]['Close'][nrows - 1]

                change_6mo.append(last - first)
                percent_6mo.append(round((last - first) / first * 100, 2))
                prices_6mo.append((first, last))
            
            else: 
                change_6mo.append(np.nan)
                percent_6mo.append(np.nan)
                prices_6mo.append(np.nan)
        
            #analyst recommendations
            recommendation.append(values[-2])
            num_analysts.append(values[-1])

    changes = pd.DataFrame(list(zip(companies, change_5day, percent_5day, change_1mo, percent_1mo, 
                                    change_6mo, percent_6mo, prices_day, prices_1mo, prices_6mo, recommendation, num_analysts)), 
                           columns = ['Company', '5-day Price Change', '5-day Change %', '1-Mo Price Change', '1-Mo Change %', 
                                      '6-mo Price Change', '6-mo Change %', '5-day (start, end) price', '1-mo (start, end) price', 
                                      '6-mo (start, end) price', 'Buy?', 'Num Analysts'])
    print("Changes calculated")
    return(changes)
####

def create_industry_df(change_df, co_dict):

    # Creates the long df for the industries used in the bar chart
    industry_recs = change_df[['Company', 'Buy?', 'Num Analysts']]

    industries = []

    for key, values in co_dict.items():
        industries.append(values[1])

    industry_recs['Industries'] = industries
    industry_recs['Buy?'] = industry_recs['Buy?'].replace(np.nan, 'No Assessment')
    industry_recs['Buy?'] = industry_recs['Buy?'].replace('none', 'No Assessment')
    industry_recs['Num Analysts'] = industry_recs['Num Analysts'].replace(np.nan, 0)

    long_df = industry_recs[['Industries', 'Buy?', 'Num Analysts']]
    long_df = long_df.groupby(['Industries', 'Buy?']).count().reset_index()
    long_df.columns = ['Industries', 'Buy?', 'Count']

    sums = long_df.groupby(['Industries'])['Count'].sum().reset_index()
    long_df = long_df.merge(sums, left_on = 'Industries', right_on = 'Industries')

    long_df['Ratio'] = round(long_df['Count_x'] / long_df['Count_y'], 2)

    ########### new code below
    
    ## consolidates the names of the companies for the stacked bar chart hover data
    
    companies = []
    industries = []
    recs = []
    combined_list = []

    for key, values in co_dict.items():
        companies.append(key)
        industries.append(values[1])
        recs.append(values[-2])
    
    combined_df = pd.DataFrame()
    combined_df['Companies'] = companies
    combined_df['Industries'] = industries
    combined_df['recs'] = recs
    
    combined_df = combined_df.groupby(['Industries', 'recs'])['Companies'].apply(list).reset_index(drop = False)
    
    co_list = combined_df['Companies']
    for ind in range(len(co_list)):
        temp = []
        if ( (len(co_list[ind]) > 3) ):
        
            for val_ind in range(len(co_list[ind])):
                if ( (val_ind % 2 == 0) & (val_ind != 0) ):
                    co_list[ind][val_ind] = '<br>' + co_list[ind][val_ind]
    
    combined_df['Companies'] = combined_df['Companies'].apply(lambda x: (str(x).replace('[', '')))
    combined_df['Companies'] = combined_df['Companies'].apply(lambda x: (str(x).replace(']', '')))
    combined_df['Companies'] = combined_df['Companies'].apply(lambda x: (str(x).replace("\'", "")))
    combined_df['recs'] = combined_df['recs'].replace('none', 'No Assessment')

    long_df['Companies'] = combined_df['Companies']
    
    ########### new code above
    
    return(long_df)
#####

def create_industry_stackedbar(long_df, color_style, color_dict, style_key):

    industry_health = px.bar(long_df, x = "Industries", y = "Ratio", color = "Buy?", #title = "long input",
                             #color_discrete_sequence=['darkviolet', 'palevioletred', 'mediumpurple', 'dodgerblue', 'mediumblue'],
                             color_discrete_sequence=color_dict[style_key],
                             #hover_name = 'Industries', 
                             hover_data = ['Buy?', 'Companies'])
                            #['darkviolet', 'palevioletred', 'mediumpurple', 'dodgerblue', 'mediumblue']
                            #['#7FD4C1', '#30BFDD', '#8690FF', '#ACD0F4', '#F7C0BB']
    #title = dict(text = f"One Month Price History for {name}", font = dict(size = 24, color = 'white'))
    customdata = np.stack((long_df['Buy?'], long_df['Companies']), axis = 1)
    industry_health.update_traces(hovertemplate = "<b>Industry</b>: %{x}" +
                              "<br><b>Buy</b>: %{customdata[0]}" +
                              "<br><b>Percentage</b>: %{y}" +
                              "<br><b>Companies</b>: %{customdata[1]}" 
                              )
    industry_health.update_layout(width = 1200, height = 500, plot_bgcolor=color_style[style_key]['plot_color_back'],
                                  paper_bgcolor=color_style[style_key]['plot_color_back'], # paper and plot were "rgba(0, 0, 0, 0)"
                                 #title = dict(text = "Buy/Sell Recommendations by Industry", font = dict(size = 24, color = 'white')),
                                 legend=dict(title_font_family="Times New Roman", font=dict(family="Courier", size=16,
                                                                                            color=color_style[style_key]['plot_font']) ) ) # color was "white"
    industry_health.update_yaxes(tickformat = '.0%', 
                                 title = dict(text = "Ratio", font = dict(size = 22), font_color = color_style[style_key]['plot_font']),
                                 #tickvals = [0, 20, 40, 60, 80, 100],
                                 tickfont = dict(size = 16, color = color_style[style_key]['plot_font']))
    industry_health.update_xaxes(title = dict(text = "Industry", font = dict(size = 22), font_color = color_style[style_key]['plot_font']),
                                 tickfont = dict(size = 16, color = color_style[style_key]['plot_font']))
    industry_health.update_annotations(font_color = color_style[style_key]['plot_font'], font_size = 22)
    industry_health.update_traces(marker_line_width = 2)
    if industry_health: #if industry_health:
        print('Stacked barchart created')
    return(industry_health)
#####

def create_table_buy_recs(possible_buy, color_style, color_dict, style_key):

    df_buy_recs = possible_buy.copy()
    df_buy_recs['Last Price'] = df_buy_recs['5-day (start, end) price'].apply(lambda x: x[1])
    df_buy_recs = df_buy_recs.drop(columns = ['5-day (start, end) price', '1-mo (start, end) price', '6-mo (start, end) price'])
    df_buy_recs = round(df_buy_recs, 2)
    df_buy_recs = df_buy_recs[['Company', 'Buy?', 'Num Analysts', 'Last Price']]

    
    ### two tables - one high level with buy/sell, num analysts and last price
    # creates the px table for the dashboard
    table_buy_recs = go.Figure(data=[go.Table(columnwidth = [180,100],
        header=dict(values=list(df_buy_recs.columns),
                    fill_color=color_style[style_key]['table_header_fill'],##### #"rgba(30,144,255, 0.7)"
                    line_color=color_style[style_key]['line_color_buy'],##### dodgerblue
                    font=dict(color = color_style[style_key]['table_font'], size = 18), ##### white
                    align=['left','center']),
        cells=dict(values=[df_buy_recs['Company'], 
                           df_buy_recs['Buy?'],
                           df_buy_recs['Num Analysts'],
                           df_buy_recs['Last Price'] ],
                   fill_color=color_style[style_key]['table_cells_fill'], ### black
                   height = 30,
                   #line_color='dodgerblue',
                   font=dict(color=color_style[style_key]['table_font'], size = 17), #### white
                   align=['left','center']))])
    table_buy_recs.update_layout(
        autosize=False,
        width=600,
        height=800, plot_bgcolor=color_style[style_key]['plot_color_back'], 
        paper_bgcolor=color_style[style_key]['plot_color_back']) # rgba(128, 128, 128, 0.1) #####
    
    if table_buy_recs: #if industry_health:
        print('Table created for analyst recommendations on stocks to buy')
    return(table_buy_recs)
#####

def create_table_buy_prices(possible_buy, color_style, color_dict, style_key):

    df_buy_prices = possible_buy.copy()
    df_buy_prices['Last Price'] = df_buy_prices['5-day (start, end) price'].apply(lambda x: x[1])
    df_buy_prices = df_buy_prices.drop(columns = ['5-day (start, end) price', '1-mo (start, end) price', '6-mo (start, end) price'])
    df_buy_prices = round(df_buy_prices, 2)
    df_buy_prices = df_buy_prices[['Company', '5-day Price Change', '5-day Change %', '1-Mo Price Change', 
                          '1-Mo Change %', '6-mo Price Change', '6-mo Change %']]
    
    # creates a plotly table of price history for each stock to buy
    table_buy_prices = go.Figure(data=[go.Table(columnwidth = [150,50],
        header=dict(values=list(df_buy_prices.columns),
                    fill_color=color_style[style_key]['table_header_fill'], #"rgba(30,144,255, 0.7)"
                    line_color=color_style[style_key]['line_color_buy'], #'dodgerblue'
                    font=dict(color = color_style[style_key]['table_font'], size = 12), #'white'
                    align='left'),
        cells=dict(values=[df_buy_prices['Company'], 
                           df_buy_prices['5-day Price Change'], 
                           df_buy_prices['5-day Change %'],
                           df_buy_prices['1-Mo Price Change'],
                           df_buy_prices['1-Mo Change %'] ,
                           df_buy_prices['6-mo Price Change'],
                           df_buy_prices['6-mo Change %'] ],
                   fill_color=color_style[style_key]['table_cells_fill'], #'black'
                   height = 30,
                   #line_color='dodgerblue',
                   font=dict(color=color_style[style_key]['table_font'], size = 12), #white
                   align=['left','center']))])
    table_buy_prices.update_layout(
        autosize=False,
        width=700,
        height=800, plot_bgcolor=color_style[style_key]['plot_color_back'], 
        paper_bgcolor=color_style[style_key]['plot_color_back']) # rgba(128, 128, 128, 0.1)
    #"rgba(0, 0, 0, 0)"
    #table_buy_prices.show()
    if table_buy_prices: #if industry_health:
        print('Table created for previous stock prices on stocks to buy')
    return(table_buy_prices)
#####

def get_prices_one_month(possible_buy, co_dict):
    
    # concat dataframes for multiple stocks to show multiple lines
    viz_data = pd.DataFrame()
    # for each company that is good to buy, add last month's data to visualize
    for name in list(possible_buy['Company']):
        temp = co_dict[name][-4]
        temp['Company'] = name
        viz_data = pd.concat([viz_data, temp])

    # 
    viz_month = viz_data.pivot(index = 'Date', columns = 'Company', values = 'Close')
    viz_month = viz_month.reset_index(drop = False)
    #viz_week = viz_month[-5:]
    print("Dataframe created for visualizing line graphs.")
    return(viz_month)
#####

def create_line_graph_buy(viz_month, possible_buy, color_style, color_dict, style_key):
    
    # this for loop creates the grid for the "all buy plots"
    specs_list = []
    for i in range(len(list(possible_buy['Company']))):
        specs_list.append([{"rowspan": 1}])
    
    # creates a tuple of title names used as a parameter for subplots
    titles = []
    for name in list(possible_buy['Company']):
        titles.append(name) # was "one month price history for xxx"
    titles = tuple(titles)

    # **creates the subplot variable used in the dashboard for each company
    all_buy_plots = make_subplots(rows = len(list(possible_buy['Company'])), #insets = [{'b': 1}],
                                 specs = specs_list, subplot_titles = titles)

    # for loop adds a "buy" graph for each company
    j = 1
    for name in list(possible_buy['Company']):
        # creates the line graph of prices
        viz_month[name] = round(viz_month[name], 2)
        fig1 = px.line(viz_month, x = viz_month['Date'], y = viz_month[name])
        fig1 = fig1.update_traces(line = {'color': color_style[style_key]['line_color_buy']})
    
        # creates the plot of points
        fig2 = px.scatter(viz_month, x = viz_month['Date'], y = viz_month[name], width = 10, height=100)
        # adds to the variables for size and color aesthetics
        sizes, colors = [12], [color_style[style_key]['line_color_buy']] ## dodgerblue 
        for i in range(len(list(viz_month[name]))):
            sizes.append(6)
            colors.append(color_style[style_key]['point_color_buy']) # gold
        fig2 = fig2.update_traces(marker = {'size': sizes, 'color': colors})
    
        fig3 = go.Figure(data = fig1.data + fig2.data)
    
        fig3.update_layout(width = 600, height = 500, margin = dict(l=20, r=20, t=50, b=20),
                      yaxis_tickformat = '$',
                      yaxis = dict(tickfont = dict(size = 16)),
                      xaxis = dict(tickfont = dict(size = 16)),
                      title = dict(text = name, # One Month Price History for {name}
                                   font = dict(size = 24, color = color_style[style_key]['plot_font'])), #white
                      xaxis_title = dict(text = "Date", font = dict(size = 18)),
                      yaxis_title = dict(text = "Closing Price", font = dict(size = 18)),
                          paper_bgcolor=color_style[style_key]['plot_color_back'],  # "rgba(0,0,0,0)"
                           plot_bgcolor=color_style[style_key]['plot_color_back']) # "rgba(0,0,0,0)"  ### IMPORTANT - transparency)

        #print(metric_figure.print_grid)
        # ** adds the fig3 data to the subplots figure
        for t in fig3.data:
            all_buy_plots.add_trace(t, row =j, col = 1)
        j += 1
    
    #all_buy_plots.update_layout(width = 600, height = 1000,
    all_buy_plots.update_layout(width = 600, height = 4000,
                                #xaxis_title = dict(text = "Date", font = dict(size = 18), font_color = 'white'),
                                yaxis_title = dict(text = "Closing Price", font = dict(size = 18), 
                                                   font_color = color_style[style_key]['plot_font']),
                                yaxis_tickformat = '$',
                                yaxis = dict(tickfont = dict(size = 16)),
                                xaxis = dict(tickfont = dict(size = 16)), 
                                plot_bgcolor=color_style[style_key]['line_buy_bground'], # "rgba(128, 128, 128, 0.1)"
                                paper_bgcolor=color_style[style_key]['line_buy_bground']) ### IMPORTANT - transparency)
              
    all_buy_plots.update_annotations(font_color = color_style[style_key]['plot_font'], font_size = 20)

    all_buy_plots.update_yaxes(tickformat = '$', 
                               title = dict(text = "Closing Price", font = dict(size = 18), 
                                            font_color = color_style[style_key]['plot_font']),
                               tickfont = dict(size = 16, color = color_style[style_key]['plot_font']))
    all_buy_plots.update_xaxes(#title = dict(text = "Date", font = dict(size = 16), font_color = 'white'),
                               tickfont = dict(size = 16, color = color_style[style_key]['plot_font']))
                           
    #all_buy_plots.show()

    if all_buy_plots: #if industry_health:
        print('Line graphs created for potential stocks to buy')
    return(all_buy_plots)
#####
#############################################################################
def calculate_stocks_owned(stocks_owned, co_dict):
    
    # appends the data frame of closing prices since buying the stock, for each stock owned

    owned_keys = list(stocks_owned.keys())

    # the ticker was dropped from the master dictionary because data could not be pulled
    for key in owned_keys:
        if (key not in list(co_dict.keys())):
            del(stocks_owned[key])


    for stock, values in stocks_owned.items():
        # add the dataframe to the stocks_owned dictionary
        if (len(co_dict[stock]) >= 6):
            prices = co_dict[stock][3].reset_index() # uses the dataframe for the past 6 months
            if (prices.shape[0] == 0):
                print(f"Could not add price history for {stock}")
                continue
        else:
            print(f"Could not add price history for {stock}")
            continue

        # subset to only the closing prices since I bought the stock
        # uses "stocks_owned" dictionary, with the first index of the values
        prices = prices[prices['Date'] >= stocks_owned[stock][0]]
        prices['Close'] = round(prices['Close'], 2)

        # calculate percentage increase/decrease since buying
        bought = stocks_owned[stock][1]
        current = prices['Close'].iloc[-1]
        change_price = round(current - bought, 2)
        change_percent = round(change_price / current * 100, 2)

        # add analyst recommendation data
        rec = co_dict[stock][6]
        num = co_dict[stock][7]

        # 
        stocks_owned[stock].append(prices) # index 2 for the daily price data
        stocks_owned[stock].append(change_price) # index 3
        stocks_owned[stock].append(change_percent) # index 4
        stocks_owned[stock].append(rec)
        stocks_owned[stock].append(num)
        
    print("Data on stocks owned has been appended to. Columns are: \n", list(stocks_owned.keys()))
    return(stocks_owned)
#####

def create_table_sell_recs(stocks_owned, color_style, color_dict, style_key):

    # ANALYST RECOMMENDATIONS - Sell
    df_stocks_owned_recs = pd.DataFrame()
    df_stocks_owned_recs['Company'] = list(stocks_owned.keys())
    rec, num = [], []

    for stock, values in stocks_owned.items():
        rec.append(values[5])
        num.append(values[6])
    df_stocks_owned_recs['Buy?'] = rec
    df_stocks_owned_recs['Num Analysts'] = num


    table_sell_recs = go.Figure(data=[go.Table(columnwidth = [90,50],
        header=dict(values=list(df_stocks_owned_recs.columns), 
                    fill_color=color_style[style_key]['table_header_fill_sell'], # "rgba(219,112,147, 0.7)"
                    line_color=color_style[style_key]['line_color_sell'], # 'palevioletred'
                    font=dict(color = color_style[style_key]['table_font'], size = 18), # white
                    align=['left','center']),
        cells=dict(values=[df_stocks_owned_recs['Company'], 
                           df_stocks_owned_recs['Buy?'], 
                           df_stocks_owned_recs['Num Analysts'] ],
                   fill_color=color_style[style_key]['table_cells_fill'], # black
                   height = 30,
                   font=dict(color=color_style[style_key]['table_font'], size = 17),
                   align=['left','center']))])
    table_sell_recs.update_layout( 
        autosize=False,
        width=600,
        height=800, plot_bgcolor=color_style[style_key]['plot_color_back'], # "rgba(0, 0, 0, 0)"
        paper_bgcolor=color_style[style_key]['plot_color_back']) # rgba(128, 128, 128, 0.1)
    #table_sell_recs.show()
    
    if table_sell_recs: #if industry_health:
        print('Table created for analyst recommendations on stocks I own!')
    return(table_sell_recs)
#####

def create_table_sell_prices(stocks_owned, color_style, color_dict, style_key):

   # prepare the dataframes for the plotly tables
    # PRICE HISTORY create a dataframe of stocks_owned and a go.table object
    df_stocks_owned_prices = pd.DataFrame()
    df_stocks_owned_prices['Company'] = list(stocks_owned.keys())
    bought_in, change_price, change_percent = [], [], []

    for stock, values in stocks_owned.items():
        bought_in.append(values[1]) # price I bought it at (cost-basis)
        change_price.append(values[3]) # price increase/decrease in USD
        change_percent.append(str(values[4]) + '%') # price percentage change

    df_stocks_owned_prices['Price Bought'] = bought_in
    df_stocks_owned_prices['Price Change'] = change_price
    df_stocks_owned_prices['Change Percentage'] = change_percent

    table_sell_prices = go.Figure(data=[go.Table(columnwidth = [100,50],
        header=dict(values=list(df_stocks_owned_prices.columns),
                    fill_color=color_style[style_key]['table_header_fill_sell'], # "rgba(219,112,147, 0.7)"
                    line_color=color_style[style_key]['line_color_sell'], # palevioletred
                    font=dict(color = color_style[style_key]['table_font'], size = 12),
                    align=['left','center']),
        cells=dict(values=[df_stocks_owned_prices['Company'], 
                           df_stocks_owned_prices['Price Bought'], 
                           df_stocks_owned_prices['Price Change'],
                           df_stocks_owned_prices['Change Percentage']],
                   fill_color=color_style[style_key]['table_cells_fill'],
                   height = 30,
                   font=dict(color=color_style[style_key]['table_font'], size = 12),
                   align=['left','center']))])
    table_sell_prices.update_layout( 
        autosize=False,
        width=700,
        height=800, plot_bgcolor=color_style[style_key]['plot_color_back'], # "rgba(0, 0, 0, 0)"
        paper_bgcolor=color_style[style_key]['plot_color_back']) # rgba(128, 128, 128, 0.1)
    #table_sell_prices.show()
    
    if table_sell_prices: #if industry_health:
        print('Table created for price history on stocks I own since I bought in!')
    return(table_sell_prices, df_stocks_owned_prices)
#####

def create_line_graph_sell(stocks_owned, color_style, color_dict, style_key):
        
    # 
    specs_list = []
    for i in range(len(list(stocks_owned.keys()))):
        specs_list.append([{"rowspan": 1}])

    # creates a tuple of title names used as a parameter for subplots
    titles = []
    for stock, values in stocks_owned.items():
    
        # pulls the dataframe of prices from the stocks owned dictionary
        data = values[2]
        # price change in USD
        if (values[3] < 0.0):
            sign = '-'
        elif (values[3] > 0.0):
            sign = '+'
        else:
            sign = ''
        change_price = abs(values[3])
        # price change by percent
        change_percent = abs(values[4])
    
        titles.append(f"<b>Price History for {stock}:<br> Current Gain = {sign}${change_price}, change is {sign}{change_percent}%<b>")
    titles = tuple(titles)

    # **creates the subplot variable used in the dashboard for each company
    all_sell_plots = make_subplots(rows = len(list(stocks_owned.keys())), insets = [{'b': 1}],
                                  specs = specs_list, subplot_titles = titles)

    # for loop adds a "buy" graph for each company
    k = 1
    for stock, values in stocks_owned.items():
    
        data = values[2]
    
        # creates the line graph of prices
        fig1 = px.line(data, x = data['Date'], y = data['Close'])
        fig1 = fig1.update_traces(line = {'color': color_style[style_key]['line_color_sell']})
    
        # creates the plot of points
        fig2 = px.scatter(data, x = data['Date'], y = data['Close'], width = 10, height=100)
        # adds to the variables for size and color aesthetics
        sizes, colors = [12], [color_style[style_key]['line_color_sell']]
        for i in range(len(list(data['Close']))):
            sizes.append(6)
            colors.append(color_style[style_key]['point_color_sell'])
        fig2 = fig2.update_traces(marker = {'size': sizes, 'color': colors})
    
        # dataframe for plotting a star at the currently-owned price point
        fig3_df = pd.DataFrame()
        fig3_df['Date'] = [values[0]] # date bought
        fig3_df['Price Bought'] = [values[1]]
    
        fig3 = px.scatter(fig3_df, x = 'Date', y = 'Price Bought')
        fig3 = fig3.update_traces(marker = {'size': [20], 'color': [color_style[style_key]['point_color_sell']], 
                                            'symbol': ['star']})
    
        fig4 = go.Figure(data = fig1.data + fig2.data + fig3.data)
    
        fig4.update_layout(width = 600, height = 500, margin = dict(l=20, r=20, t=50, b=20),
                           yaxis_tickformat = '$',
                           yaxis = dict(tickfont = dict(size = 16)),
                           xaxis = dict(tickfont = dict(size = 16)),
                           title = dict(text = f"Price History for {stock}: <br>Current Gain = {sign}${change_price}, change is {sign}{change_percent}%", font = dict(size = 24)),
                           xaxis_title = dict(text = "Date", font = dict(size = 18)),
                           yaxis_title = dict(text = "Closing Price", font = dict(size = 18)), 
                           paper_bgcolor=color_style[style_key]['plot_color_back'], # "rgba(0,0,0,0)"
                           plot_bgcolor=color_style[style_key]['plot_color_back']) ### IMPORTANT - transparency
    
        for t in fig4.data:
            all_sell_plots.add_trace(t, row = k, col = 1)
        k += 1

    #
    all_sell_plots.update_layout(width = 600, height = 3000,
                                xaxis_title = dict(text = "Date", 
                                                   font = dict(size = 18, color = color_style[style_key]['plot_font'])),
                                yaxis_title = dict(text = "Closing Price", 
                                                   font = dict(size = 18, color = color_style[style_key]['plot_font'])),
                                yaxis_tickformat = '$',
                                yaxis = dict(tickfont = dict(size = 16)),
                                xaxis = dict(tickfont = dict(size = 16)), 
                                 plot_bgcolor=color_style[style_key]['line_buy_bground'], # "rgba(128, 128, 128, 0.1)"
                                 paper_bgcolor=color_style[style_key]['line_buy_bground']) ### IMPORTANT - transparency

    # change title size to 24
          
    all_sell_plots.update_annotations(font_color = color_style[style_key]['plot_font'], font_size = 20)

    all_sell_plots.update_yaxes(tickformat = '$', 
                               title = dict(text = "Closing Price", font = dict(size = 18), 
                                            font_color = color_style[style_key]['plot_font']),
                               tickfont = dict(size = 16, color = color_style[style_key]['plot_font']))
    all_sell_plots.update_xaxes(title = dict(text = "Date", font = dict(size = 16), 
                                             font_color = color_style[style_key]['plot_font']),
                               tickfont = dict(size = 16, color = color_style[style_key]['plot_font']))
    return(all_sell_plots)


########## line graph multiple equities
def calculate_daily_percent(industry_names, company_tickers):
    '''
    input: list of industry names to subset down to
    Create new dataframe where the columns are the company tickers
    Rows are each day in the past month - datetime for a line graph should be days
    Cells hold values for % price change from the day before (ex. 4 Mar column would hold %change for [(4 Mar - 3 Mar) / 4 Mar])
    '''
    
    ###### create master dataframe
    # create the dataframe that will hold the %changes 
    df_dates = company_tickers['Microsoft'][4]
    index_dates = list(df_dates['Date'])
    
    # ** will be used for all companies
    df_daily_perc = pd.DataFrame(index = index_dates)
    df_daily_perc = df_daily_perc[1:]
    
    ###### loop through the company_tickers
    for key, values in company_tickers.items():
        
        if (company_tickers[key][1] in industry_names):
            # holds all closing prices for this company - use the 1-month prices dataframe - index 4
            df_today = company_tickers[key][4]
            
            ######### variables for calculating price changes - use dataframes (not lists) because it's faster
            # dataframe holds the prices for time (t - 1)
            df_yesterday = df_today.copy()
            df_yesterday = df_yesterday[:-1]
            price_yesterday = list(df_yesterday['Close']) # holds the prices for (t - 1)
            
            # dataframe holds prices for time (t)
            df_today = df_today[1:]
            df_today = df_today[['Date', 'Close']]
            df_today.columns = ['Date', 'Price Today (t)']
            df_today['Price Yesterday (t-1)'] = price_yesterday
            
            # calculate % change for each day
            df_today['Amt Change'] = (df_today['Price Today (t)'] - df_today['Price Yesterday (t-1)'])
            df_today['% Change'] = round((df_today['Amt Change'] / df_today['Price Yesterday (t-1)']) * 100, 2)
            
            # now assign the list back to the master df with the company name as the key
            percent_values = list(df_today['% Change'])
            
            df_daily_perc[key] = percent_values
            
    return(df_daily_perc)


def create_line_graph_multiple(df_daily_perc, color_palette = ['tan'], additional_colors = []):
    
    num_colors = len(df_daily_perc.columns)

    rates_line_graph = px.line(df_daily_perc, x=df_daily_perc.index, y=df_daily_perc.columns, 
                  color_discrete_sequence = color_palette + additional_colors, #color_dict['Beach'][:num_colors]
                  width=1400, height=800
                 )

    ####### modify the hover text to include, for each day:
        # add '%' to the value
        # buy/sell recommendation
        # price for each day

    #######

    #######
    min_val, max_val = 0, 0
    for col in df_daily_perc.columns:
        min_temp = min(list(df_daily_perc[col]))
        max_temp = max(list(df_daily_perc[col]))
        if (min_temp < min_val):
            min_val = min_temp
        if (max_temp > max_val):
            max_val = max_temp
    
    y_range = (max_val - min_val) # range for y-axis
    if (y_range > 2.0):
        y_range = math.ceil(y_range / 2.) * 2

    y_increment = round(y_range / 4, 1) # amount to add to each tick

    tick_vals = [round(min_val, 1)]
    for i in range(4):
        tick_vals.append(round(tick_vals[i] + y_increment, 1))
    tick_text = [f"{val}%" for val in tick_vals] #generate text for your ticks
    ########

    
    rates_line_graph.update_layout(
        # set tick mode to array, tickvals to your vals calculated and tick text  to the text genrated
        yaxis={"tickmode":"array","tickvals":tick_vals, "ticktext": tick_text,
              },
        #title=dict(text=f'\nDaily % Changes for All Stocks in an Industry', font=dict(size=26), x = 0.5), 
        xaxis_title={"text": "Last 30 Days", "font": dict(size = 20)},
        yaxis_title={"text": "Percentage<br>Change", "font": dict(size = 20)},
        legend_title_text = 'Company',
        plot_bgcolor = "grey", #gainsboro
        paper_bgcolor = 'lightgray'
    )
    
    ##########

    #rates_line_graph.show()
    return(rates_line_graph)



def show_dashboard(color_palette = ['tan'], additional_colors = []):

    display(HTML("<style>div.output_scroll { height: 100em; }</style>"))
    app = JupyterDash(__name__, external_stylesheets=external_stylesheets)
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    print("if a link to the dashboard is not provided, copy the following url into a new browser tab: 'http://127.0.0.1:8050/'\n\n------------------")

    # creates the dashboard using the figures, tables, and markdown.
    app.layout = html.Div(
        [ 
            html.H1("Equity Analysis Dashboard", style = {'font-weight': 'bold', 'float': 'center', 'font_size': '20px', 'font-family': 'courier',
                                              'color': color_style[style_key]['heading_font'], 'marginLeft': '30%', 'margin-bottom': 5}),
            dcc.Markdown(children = ""),

    ########### H3 section 1
            html.Div([
                html.H3("Daily Rates of Change - Choose each industry", style = {#'font-weight': 'bold', 
                                                          'font_size': '20px', 'font-family': 'courier',
                                                                                'textAligh': 'center', 'marginLeft': '30%', #'marginRight': '80%',
                                                                               'margin-bottom': -30, 'margin-top': 100,
                                                                #"backgroundColor": color_style[style_key]['heading_color']
                                                                               }),
                dcc.Dropdown(list(set(list(long_df['Industries']))), list(set(list(long_df['Industries'])))[:2], 
                             multi= True, id = 'dropdown-2', style={'width': '50%'}),
                dcc.Graph(id="graph", style = {'marginLeft': '12%'})
                #dcc.Checklist(id = 'checklist', 
                #              options = list(set(list(long_df['Industries']))),
                #              value = list(set(list(long_df['Industries'])))[:2],
                #              inline = True
                #             ) ###

            ], 
        style = {'width':'100%', 'float':'left', 'backgroundColor': color_style[style_key]['plot_color_dash'], "maxHeight": "1200px", "overflow": "scroll",
                        'color': color_style[style_key]['heading_font']}
        ),

    ########### H3 section 2

            html.Div([
                html.H3("Industry Overview and Analyst Recommendations", style = {#'font-weight': 'bold', 
                                                                                  'font_size': '20px', 'font-family': 'courier',
                                                                                'textAligh': 'center', 'marginLeft': '20%', #'marginRight': '80%',
                                                                               'margin-bottom': -50, 'margin-top': 100,
                                                                #"backgroundColor": color_style[style_key]['heading_color']
                                                                               }),
                dcc.Graph(figure=industry_barStacked, style = {'marginLeft': '12%'})
            ], style = {'width':'100%', 'float':'left', 'backgroundColor': color_style[style_key]['plot_color_dash'], "maxHeight": "800px", "overflow": "scroll",
                        'color': color_style[style_key]['heading_font']}),

    ########### H3 section 3
            html.Div([
                html.H3("1-Month Charts", style = {#'font-weight': 'bold', 
                                                   'font_size': '12px', 'textAligh': 'center',
                                                                           'font-family': 'courier',
                                                                            'marginLeft': '15%', 'margin-bottom': -20, 'margin-top': 20,
                                                                #"backgroundColor": color_style[style_key]['heading_color']
                                                                }),
                dcc.Graph(figure=all_buy_plots)
            ], style = {#'marginLeft': '5%',
                        'width':'35%', # was 35% with no margin or empty section to left
                        'float':'left', 'backgroundColor': color_style[style_key]['plot_color_dash'], 'horizontal-align': 'right', 'vertical-align': 'middle', #'rgba(70,130,180, 0.7)'
                        "maxHeight": "700px", "overflow": "scroll", 'color': color_style[style_key]['heading_font'], 'font_size': '40px'}), #### 
                    ### change height to 800 for charts, 400 and 400 for tables
            #####
            html.Div([
                html.H3("Analyst Recommendations", style = {#'font-weight': 'bold', 
                                                            'font_size': '6px', 'textAligh': 'center',
                                                              'font-family': 'courier',
                                                              'marginLeft': '20%', 'margin-bottom': -80, 'margin-top': 20,
                                                                #"backgroundColor": color_style[style_key]['heading_color']
                                                          }),
                dcc.Graph(figure=table_buy_recs)
            ], style = {'width':'30%', 'float':'left', 'backgroundColor': color_style[style_key]['plot_color_dash'], "maxHeight": "700px", 
                        "overflow": "scroll", 'color': color_style[style_key]['heading_font']}),
            ####
            html.Div([
                html.H3("Price % Increase / Decrease", style = {#'font-weight': 'bold', 
                                                                'font_size': '20px', 'textAligh': 'center',
                                                              'font-family': 'courier',
                                                              'marginLeft': '20%', 'margin-bottom': -80, 'margin-top': 20,
                                                                #"backgroundColor": color_style[style_key]['heading_color']
                                                              }),
                dcc.Graph(figure=table_buy_prices)
            ], style = {'width':'35%', 'float':'left', 'backgroundColor': color_style[style_key]['plot_color_dash'], "maxHeight": "700px", 
                        "overflow": "scroll", 'color': color_style[style_key]['heading_font']}),

        ],
        style = {"backgroundColor": color_style[style_key]['heading_color']} # dashboard background all sections

    )

    ######## callback for the dropdown for the rates of change line graph
    @app.callback(
        Output("graph", "figure"),
        Input('dropdown-2', "value"))

    def update_line_graph(industries, color_palette = color_palette, additional_colors = additional_colors):
        industry_names = industries
        df_daily_perc = calculate_daily_percent(industry_names) # dataframe
        fig = create_line_graph_multiple(df_daily_perc, color_palette = color_palette,
                                         additional_colors = additional_colors) # line graph
        return(fig)
    ########


    host = '127.0.0.1'
    if __name__ == '__main__':
        #http://127.0.0.1:8050/
        #app.run_server(mode='inline', debug=True, port=8050)
        app.run_server(mode='external', host = host, debug=True, port=8050)