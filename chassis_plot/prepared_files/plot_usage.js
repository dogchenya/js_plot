
var plot_usage_objs = {
  ma_type: '',
  ma_value: 0,
  data_len: data_date.length,
  feedback_val: {
    x: data_date,
    y: feedback_val,
    type: 'scatter',
    name: 'feedback_val',
    mode: 'lines',
    line: {
      color: '#636EFA',
    },
    legendgroup: '1',
    legendgrouptitle: {
      text: "feedback value left",
      font: {
        size: 20,
      }
    },
  },
  layout: {
    title: {
      text: node_name + "(" + node_meaning + ")",
      font: {
        size: 50,
      },
    },
    height: parseInt(innerHeight * 0.8),
    //autosize: true,
    yaxis: {
      title: 'feedback value',
    },
    yaxis2: {
      title: 'usage(Bytes)',
      side: 'right',
      overlaying: 'y',
    },
    legend: {
      //orientation: "h",
      font: {
        size: 18,
      },
      groupclick: "toggleitem",
    },
  },
}

function calcMa() {
  var data_date_ma = []
  var data_value_ma = []
  var ma_value = plot_usage_objs.ma_value
  var ma_date = parseInt(plot_usage_objs.ma_value / 2)
  var ma_num = 0;
  var ma_sum = 0;
  var data = plot_usage_objs[plot_usage_objs.ma_type]
  // TODO: check this
  for (var i = 0; i < plot_usage_objs.data_len; i++) {
    if (ma_num < ma_value) {
      ma_sum += data.y[i];
      ma_num++;
    } else {
      data_date_ma.push(data_date[i - ma_date]);
      data_value_ma.push(ma_sum / ma_value);
      ma_sum = data.y[i];
      ma_num = 1;
    }
  }
  plot_usage_objs.ma = {
    x: data_date_ma,
    y: data_value_ma,
    type: 'scatter',
    name: data.name + '_ma ' + ma_value.toString(),
    mode: 'lines',
    line: {
      color: '#222222',
    },
    yaxis: data.yaxis,
    legendgroup: data.legendgroup,
  };
}

function getData() {
  var new_ma_type = $('#ma_type_selector').val();
  var new_ma_value = parseInt($('#ma_value_selector').val());
  if ((new_ma_value != plot_usage_objs.ma_value) || (new_ma_type != plot_usage_objs.ma_type)) {
    plot_usage_objs.ma_value = new_ma_value;
    plot_usage_objs.ma_type = new_ma_type;
    calcMa();
  }
  return [plot_usage_objs.feedback_val];
}

function updateGraphPoint() {
  Plotly.react("figure", getData(), plot_usage_objs.layout);
}

function showCustomMaValueChange() {
  $('#custom_ma').show();
}

function addCustomMa() {
  var value = $('#custom_ma_value').val()

  $('#ma_value_selector').prepend("<option value='" + value + "' selected='selected'>" + value + "</option>");
  $('#custom_ma').hide();

  Plotly.react("figure", getData(), plot_usage_objs.layout);
}

function onMaTypeChange(value) {
  updateGraphPoint();
}

function onMaValueChange(value) {
  if (value == "custom") {
    showCustomMaValueChange();
  } else {
    updateGraphPoint();
  }
}


$(document).ready(function () {
  $('#side_nav').html(side_html)

  $("#first_letter_" + node_name.charAt(0)).addClass('active');
  $("#first_letter_" + node_name.charAt(0)).parent().children('ul').show();
  $("#node_" + node_name).addClass("selected");
  $('#side_nav').scrollTop($("#node_" + node_name).offset().top);

  $('.sidenav li').on('click', 'a', function (e) {
    if ($(this).parent().children('ul').length) {
      e.preventDefault();
      $(this).addClass('active');
      $(this).parent().children('ul').slideDown();
    }
  });

  $('.sidenav li').on('click', 'a.active', function (e) {
    e.preventDefault();
    $(this).removeClass('active');
    $(this).parent().children('ul').slideUp();
  });

  $("#ma_type_selector").val($("#ma_type_selector option:first").val());
  $("#ma_value_selector").val($("#ma_value_selector option:first").val());
  $('#custom_ma').hide();

  Plotly.newPlot("figure", getData(), plot_usage_objs.layout);
});

