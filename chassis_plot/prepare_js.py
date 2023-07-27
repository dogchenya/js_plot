#!/usr/bin/python3
# -*- coding: utf-8 -*-

import plotly.graph_objects as go
import shutil
import os
import re
import time
import xlrd
import argparse
import sys
import cProfile
from datetime import datetime

folder = "chassis_log/"
prepared_files_folder = "prepared_files"
template_js_file_path = "template.html"
ref_table = "./ref_table.xls"
need_generate_img = True

# analysis_ref_table_device_data = [
#     {'key_or_name':'battery_vol_adc', 'id': 0, 'meaning':''}, 
#     {'key_or_name':'relay',           'id': 2, 'meaning':'继电器状态'}, 
#     ]

# analysis_ref_table_other_device_data = [
#     {'key_or_name':'motor_mode',   'id': 3, 'meaning':''}, 
#     {'key_or_name':'mcu_type',     'id': 5, 'meaning':''}, 
#     ]

analysis_ref_table_device_data = []
analysis_ref_table_other_device_data = []
log_key_list = {'GetDeviceData:': analysis_ref_table_device_data, 'GetOtherDeviceData:': analysis_ref_table_other_device_data}


def str2sec(str):
    #print(str.split(':')) #['16', '37', '30']
    h , m ,s = str.split(':')  #strip去空格
    sec = int(h)*3600 + int(m)*60 + int(s) #算出秒数
    return int(sec)

def find_ref_dirt(key_or_name, array_data):
  dirt_ret = None
  for item_data in array_data:
    if item_data['id'] == key_or_name:
      dirt_ret = item_data
      return dirt_ret

  return dirt_ret


def precess_file(file, node_data_length, nodes_map, nodename_2_meaning):
  last_time = None
  time_count = 100000
  for line in open(file).readlines()[1:]:
    line_sp = line.split('\t')
    if len(line_sp[0].split()) < 2:
      continue
    
    if last_time == line_sp[0].split()[1]:
      time_count = time_count + 1
    else:
      time_count = 100000
    last_time = line_sp[0].split()[1]

    find_key = None
    for log_key in log_key_list.keys():
      if log_key in line:
        find_key = log_key
        break
    if find_key == None:
      continue

    p1 = re.compile(r'[(](.*?)[)]', re.S)
    rets_find = re.findall(p1, line)
    a1 = line_sp[0].split()[0] + ' ' + line_sp[0].split()[1] + '.' + str(time_count)
    datetime_obj = datetime.strptime(a1, "%Y/%m/%d %H:%M:%S.%f")
    for item in rets_find:
      value = None
      value = item.split(',')[1]
      if value == None:
        continue
      dirt_ret = find_ref_dirt(item.split(',')[0], log_key_list[find_key])
      if dirt_ret == None:
        continue

      node_name = dirt_ret['key_or_name']
      meaning = dirt_ret['meaning']

      values = [datetime_obj, value]
      if not node_name in nodes_map:
        nodename_2_meaning[node_name] = meaning
        nodes_map[node_name] = [[]for i in range(node_data_length)]
      if len(values) < node_data_length:
        continue
      for i in range(node_data_length):
        nodes_map[node_name][i].append(values[i])   

def generate_node_info(output, template_html, nodes_map, nodename_2_meaning):
  side_js = open(os.path.join(output, "side.js"), "w")
  side_js.write("var side_html = '")

  index_html = open("index.html", "w")
  inner_index_html = open(os.path.join(output, "index.html"), "w")
  index_html.write("<!DOCTYPE html><html><body>\n")
  index_html.write('<head><link rel="stylesheet" href="%s/style_index.css"></head>\n' % (output))
  inner_index_html.write("<!DOCTYPE html><html><body>\n")
  inner_index_html.write('<head><link rel="stylesheet" href="style_index.css"></head>\n')

  node_names = list(nodes_map.keys())
  node_names.sort()

  first_letter = node_names[0][0]
  index_main = []
  inner_index_main = []
  index_side = []
  index_main.append('<h1 id="first_letter_%s">%s</h1>\n' % (first_letter, first_letter))
  inner_index_main.append('<h1 id="first_letter_%s">%s</h1>\n' % (first_letter, first_letter))
  index_side.append(first_letter)
  side_js.write('<ul><li><a href="#" id="first_letter_%s">%s</a><ul>' % (first_letter, first_letter))

  for node_name in node_names:
    node = nodes_map[node_name]
    meaning = nodename_2_meaning[node_name]
    meaning = meaning.replace('\n', ',')
    meaning = meaning.replace('->', ':')
    js_file = os.path.join(output, node_name + ".data.js")
    with open(js_file, "w") as f:
      timestamps = node[0]
      #timestamps = [datetime.fromtimestamp(float(x)) for x in node[0]]
      feedback_val = [float(x) for x in node[1]]
      f.write("var io_accounting_support = true;\n")
      f.write("var node_name = '%s';\n" % (node_name))
      f.write("var node_meaning = '%s';\n" % (meaning))
      f.write("var data_date = [" + ','.join(['"%s"' % str(x) for x in timestamps]) + "];\n")
      f.write("var feedback_val = [" + ','.join(node[1]) + "];\n")

    if need_generate_img:
      fig = go.Figure()
      fig.add_trace(go.Scatter(x=timestamps, y=feedback_val, mode='lines', name=node_name, legendgroup='1',))
      fig.update_layout(
          title=dict(text=node_name, font=dict(size=50)),
          yaxis=dict(title='usage(%)',),
          yaxis2=dict(title='usage(Bytes)', side='right', overlaying='y',),
          legend=dict(font=dict(size=18), x=1.05),
      )
      fig.write_image(os.path.join(output, node_name + ".snapshot.png"), width=800, height=600)

    html_file = os.path.join(output, node_name + ".data.html")
    with open(html_file, "w") as f:
      f.write(template_html.replace("###NODE_NAME###", node_name))

    if first_letter != node_name[0]:
      first_letter = node_name[0]
      index_main.append('<h1 id="first_letter_%s">%s</h1>\n' % (first_letter, first_letter))
      inner_index_main.append('<h1 id="first_letter_%s">%s</h1>\n' % (first_letter, first_letter))
      index_side.append(first_letter)
      side_js.write('</ul></li><ul><li><a href="#" id="first_letter_%s">%s</a><ul>' % (first_letter, first_letter))

    side_js.write('<li><a href="%s" id="node_%s">%s</a></li>' % (node_name + ".data.html", node_name, node_name))
    index_main.append('<a href="%s/%s.data.html"><img src="%s/%s.snapshot.png"></a>\n' %
                      (output, node_name, output, node_name))
    inner_index_main.append('<a href="%s.data.html"><img src="%s.snapshot.png"></a>\n' %
                            (node_name, node_name))

  side_js.write("</ul></li></ul>';")
  side_js.close()

  index_html.write('<div class="sidenav">\n')
  inner_index_html.write('<div class="sidenav">\n')
  for first_letter in index_side:
    index_html.write('<a href="#first_letter_%s">%s</a>\n' % (first_letter, first_letter))
    inner_index_html.write('<a href="#first_letter_%s">%s</a>\n' % (first_letter, first_letter))

  index_html.write(
      '</div><div class="main">\n')
  index_html.writelines(index_main)
  index_html.write("</div></body></html>\n")
  index_html.close()
  inner_index_html.write(
      '</div><div class="main">\n')

  inner_index_html.writelines(inner_index_main)
  inner_index_html.write("</div></body></html>\n")
  inner_index_html.close()

def generate(files, node_data_length):
  nodes_map = {}
  nodename_2_meaning = {}
  files.sort()
  
  for file in files:
    precess_file(os.path.join(folder, file), node_data_length, nodes_map, nodename_2_meaning)

  template_html = open(template_js_file_path).read()

  base_path = files[0].split('.')[0]
  output = "data"
  os.makedirs(os.path.join(base_path, output), exist_ok=True)
  for file in os.listdir(prepared_files_folder):
    shutil.copy(os.path.join(prepared_files_folder, file), os.path.join(base_path, output, file))

  os.chdir(base_path)
  generate_node_info(output, template_html, nodes_map, nodename_2_meaning)
  os.chdir("..")

def start_time_in_log(folder, file):
  timeStamp = 0
  with open(os.path.join(folder, file) ,'r') as f:
    for line in f:
      line_sp = line.split('\t')
      if len(line_sp[0].split()) < 2:
        continue
      
      tm_str = line_sp[0].split()[0]+ ' ' + line_sp[0].split()[1]
      timeArray = time.strptime(tm_str, "%Y/%m/%d %H:%M:%S")
      timeStamp = int(time.mktime(timeArray))
      
      #   time_local = time.localtime(11994630486)
      #   dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
      break
  return timeStamp

def split_files(folder):
  files = os.listdir(folder)
  files.sort()
  res = []
  file_list = []
  last_startup_time = None
  for file in files:
    startup_time = start_time_in_log(folder, file)
    if last_startup_time == None:
      last_startup_time = startup_time
      file_list.append(file)
    elif last_startup_time + 3600 != startup_time:
      last_startup_time = startup_time
      res.append(file_list)
      file_list = [file]
    else:
      file_list.append(file)
  res.append(file_list)
  return res

def read_ref_table_from_xlsx():
  data = xlrd.open_workbook(ref_table)
  device_data_table = data.sheet_by_name('DeviceData')
  # DeviceData
  for i in range(1, 132):
    ref_table_device_data_item = {}
    ref_table_device_data_item['id'] = device_data_table.cell_value(i,0)
    ref_table_device_data_item['key_or_name'] = device_data_table.cell_value(i,1)
    ref_table_device_data_item['meaning'] = device_data_table.cell_value(i,2)
    analysis_ref_table_device_data.append(ref_table_device_data_item)
  # OtherDeviceData
  device_data_table = data.sheet_by_name('OtherDeviceData')
  for i in range(1, 137):
    ref_table_other_device_data_item = {}
    ref_table_other_device_data_item['id'] = device_data_table.cell_value(i,0)
    ref_table_other_device_data_item['key_or_name'] = device_data_table.cell_value(i,1)
    ref_table_other_device_data_item['meaning'] = device_data_table.cell_value(i,2)
    analysis_ref_table_other_device_data.append(ref_table_other_device_data_item)

if __name__ == "__main__":
  # node_data_length = 2
  # file = 'chassis-1-15.log'
  # nodes_map = {}
  # nodename_2_meaning = {}
  # read_ref_table_from_xlsx()
  # cProfile.run('precess_file(os.path.join(folder, file), node_data_length, nodes_map, nodename_2_meaning)')

  parser = argparse.ArgumentParser(description=(
        'Visual Chssis Data.'
    ))
  add = parser.add_argument
  add('-s','--slience', dest='keep_slience', action='store_true', default=None,
        help="No generate thumbnail to save time.")
  args=sys.argv[1:]
  parsed_args, unknown_args = parser.parse_known_args(args)
  need_generate_img = parsed_args.keep_slience == None or parsed_args.keep_slience == False

  read_ref_table_from_xlsx()
  node_data_length = 2
  for files in split_files(folder):
    generate(files, node_data_length)