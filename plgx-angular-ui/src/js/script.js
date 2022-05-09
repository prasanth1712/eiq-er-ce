
$(document).ready(function () {
  $('[data-toggle="popover"]').popover({
    'container': '#pf-timeline',
    'placement': 'top'
  });
});

$(document).on('click', '.drop', function () { $(this).popover('show'); });

$(document).on('click', '.grid', function () { $('[data-toggle="popover"]').popover('hide'); });

const ONE_MILLISEC = 1,

  ONE_SEC = 1 * 1000,
  ONE_MINUTE = 60 * 1000,

  ONE_HOUR = 60 * 60 * 1000,
  ONE_DAY = 24 * ONE_HOUR,
  ONE_WEEK = 7 * ONE_DAY,
  ONE_MONTH = 30 * ONE_DAY,

  SIX_MONTHS = 6 * ONE_MONTH;
var alert_time = alert.time;
var data = [],
  start = new Date((alert_time - 30) * 1000),
  today = new Date((alert.time * 1000 + 30000));

for (var x in jsonFilteredArray) { //json lives in external file for testing
  data[x] = {};
  data[x].name = jsonFilteredArray[x].name;
  data[x].jsonObjectOfEvents = jsonFilteredArray[x].jsonObjectOfEvents;
  data[x].data = [];
  for (var y in jsonFilteredArray[x].data) {
    data[x].data.push({});
    for (var key in jsonFilteredArray[x].data[y]) {

      data[x].data[y][key] = jsonFilteredArray[x].data[y][key];

    }
    data[x].data[y].date = new Date(jsonFilteredArray[x].data[y].date);  //set the date
    // data[x].data[y].date = new Date(jsonFilteredArray[x].data[y].date);

    // console.log(data[x].data[y]);

  }


  $('#timeline-selectpicker').append('<option>' + data[x].name + '</option>');
  if (data[x].jsonObjectOfEvents.show_by_default) {
    data[x].display = true;
  }
}

var selectedEventsArray = [];
// for (var y in jsonObjectOfEvents) {
for (let x = 0; x < jsonFilteredArray.length; x++) {
  if (jsonFilteredArray[x].jsonObjectOfEvents.show_by_default) {
    selectedEventsArray.push(jsonFilteredArray[x].jsonObjectOfEvents.display_name)
  }

  // $('#timeline-selectpicker').append('<option>' + jsonObjectOfEvents[y].display_name + '</option>');

}

$('#timeline-selectpicker').selectpicker('val', selectedEventsArray);

let actionList = ["FILE_DELETE", "FILE_RENAME", "FILE_WRITE", "HTTP_REQUEST", "SOCKET_CLOSE", "SOCKET_CONNECT", "PROC_CREATE", "DNS_LOOKUP"];

for (let k = 0; k < actionList.length; k++) {
  $('#timeline-selectpicker-action').append('<option>' + actionList[k] + '</option>');
}

$('#timeline-selectpicker-action').selectpicker('selectAll');

var timeline = d3.chart.timeline()
  .end(today)
  .start(start)
  .minScale(1)
  .maxScale(60).eventGrouping(1000)
  .eventClick(function (el) {
    var eventsData = document.getElementById('eventsData');
    var length = 1;
    alert_table.clear();

    if (el.hasOwnProperty("events")) {
      length = el.events.length;
      for (let index = 0; index < el.events.length; index++) {
        alert_table.row.add(el.events);


      }
    } else {
      alert_table.row.add([1]);

    }
    alert_table.page.len(length);

    alert_table.draw();
    while (eventsData.firstChild) eventsData.removeChild(eventsData.firstChild);

    if (el.hasOwnProperty('events')) {


      for (let i = 0; i < el.events.length; i++) {
        // delete el.events[i].utc_time;
        // delete el.events[i].time;
        // delete el.events[i].process_guid;

        var TableRow = '';

        TableRow += '<tr><td>' +
          '<div class="card" style="margin-bottom: 0.2rem;">' + '<div class="card-header" id="label' + el.events[i].eid + '">' +
          '<h5 class="mb-0" style="">' + '<button class="btn dropdown-toggle" data-toggle="collapse" data-target="#' + el.events[i].eid + '" aria-expanded="true" aria-controls="' + el.events[i].eid + '">'
          + el.events[i].eid
          + '</button>'
          + '</h5>'
          + '</div>'
          + '<div id="' + el.events[i].eid + '" class="collapse" aria-labelledby="label' + el.events[i].eid + '" data-parent="#accordion2">'
          + '<div class="card-body ">'
          + '<div id ="' + el.events[i].eid + 'column_data_for_muliple">'
          + '</div>'
          + '</div>'
          + '</div>'
          + '</div>';
        TableRow += '</td></tr>';

        $('#eventsData').append(TableRow);

        var tbl = document.createElement("table");
        tbl.setAttribute("class", "table table-striped- table-bordered table-hover table-checkable");
        tbl.setAttribute("style", "margin-bottom: 0rem;");
        for (let child in el.events[i]) {
          if (child === 'date') {

          } else
            if (child === 'domain_name' || child === 'md5') {
              var data = el.events[i][child];
              var domain_md5_link
              if (child === 'domain_name') {
                domain_md5_link = "https://www.virustotal.com/#/domain/" + data.substring(1, data.length);
              } else {
                domain_md5_link = "https://www.virustotal.com/#/file/" + data + "/detection";

              }
              var row = document.createElement("tr");
              var cell1 = document.createElement("td");
              var cell2 = document.createElement("td");
              var firstCellText = document.createTextNode(child);
              var secondCellText = document.createTextNode(el.events[i][child]);
              var atag = document.createElement("a");
              atag.target = "_blank";
              atag.style.color = "blue";
              atag.href = domain_md5_link;
              cell1.appendChild(firstCellText);
              cell1.style.fontSize = "11px";
              cell1.style.fontWeight = 600;
              cell1.style.wordBreak = "break-all";
              cell1.style.minWidth = "75px"
              atag.appendChild(secondCellText);
              cell2.appendChild(atag);
              cell2.style.fontWeight = 500;
              cell2.style.fontSize = "10px";
              cell2.style.wordBreak = "break-all";
              row.appendChild(cell1);
              row.appendChild(cell2);
              tbl.appendChild(row);
            } else {
              var row = document.createElement("tr");
              var cell1 = document.createElement("td");
              var cell2 = document.createElement("td");
              var firstCellText = document.createTextNode(child);
              var secondCellText = document.createTextNode(el.events[i][child]);
              cell1.appendChild(firstCellText);
              cell1.style.fontSize = "11px";
              cell1.style.fontWeight = 600;
              cell1.style.wordBreak = "break-all";
              cell1.style.minWidth = "75px"
              cell2.appendChild(secondCellText);
              cell2.style.fontWeight = 500;
              cell2.style.fontSize = "10px";
              cell2.style.wordBreak = "break-all";
              row.appendChild(cell1);
              row.appendChild(cell2);
              tbl.appendChild(row);
            }
        }

        var column_data_for_muliple = document.getElementById(el.events[i].eid + 'column_data_for_muliple');
        if (column_data_for_muliple) {
          column_data_for_muliple.appendChild(tbl);
        }
      }
    } else {
      // delete el.utc_time;
      // delete el.time;
      // delete el.process_guid;

      // for (let i=0; i < el.events.length; i++){

      var TableRow = '';

      TableRow += '<tr><td>' +
        '<div class="card" style="margin-bottom: 0.2rem;">' + '<div class="card-header" id="label' + el.eid + '">' +
        '<h5 class="mb-0">' + '<button class="btn dropdown-toggle" data-toggle="collapse" data-target="#' + el.eid + '" aria-expanded="true" aria-controls="' + el.eid + '">'
        + el.eid
        + '</button>'
        + '</h5>'
        + '</div>'
        + '<div id="' + el.eid + '" class="collapse" aria-labelledby="label' + el.eid + '" data-parent="#accordion2">'
        + '<div class="card-body ">'
        + '<div id ="' + el.eid + 'column_data_for_muliple">'
        + '</div>'
        + '</div>'
        + '</div>'
        + '</div>';
      TableRow += '</td></tr>';

      $('#eventsData').append(TableRow);
      var tbl = document.createElement("table");
      tbl.setAttribute("class", "table table-striped- table-bordered table-hover table-checkable");
      tbl.setAttribute("style", "margin-bottom: 0rem;");

      for (let child in el) {
        if (child === 'date') {

        } else
          if (child === 'domain_name' || child === 'md5') {
            var data = el[child];
            var domain_md5_link
            if (child === 'domain_name') {
              domain_md5_link = "https://www.virustotal.com/#/domain/" + data.substring(1, data.length);
            } else {
              domain_md5_link = "https://www.virustotal.com/#/file/" + data + "/detection";

            }
            var row = document.createElement("tr");
            var cell1 = document.createElement("td");
            var cell2 = document.createElement("td");
            var firstCellText = document.createTextNode(child);
            var secondCellText = document.createTextNode(el[child]);
            var atag = document.createElement("a");
            atag.target = "_blank";
            atag.style.color = "blue";
            atag.href = domain_md5_link;
            cell1.appendChild(firstCellText);
            cell1.style.fontSize = "11px";
            cell1.style.fontWeight = 600;
            cell1.style.wordBreak = "break-all";
            cell1.style.minWidth = "75px"
            atag.appendChild(secondCellText);
            cell2.appendChild(atag);
            cell2.style.fontWeight = 500;
            cell2.style.fontSize = "10px";
            cell2.style.wordBreak = "break-all";
            row.appendChild(cell1);
            row.appendChild(cell2);
            tbl.appendChild(row);
          } else {
            var row = document.createElement("tr");
            var cell1 = document.createElement("td");
            var cell2 = document.createElement("td");
            var firstCellText = document.createTextNode(child);
            var secondCellText = document.createTextNode(el[child]);
            cell1.appendChild(firstCellText);
            cell1.style.fontSize = "11px";
            cell1.style.fontWeight = 600;
            cell1.style.wordBreak = "break-all";
            cell1.style.minWidth = "75px"
            cell2.appendChild(secondCellText);
            cell2.style.fontWeight = 500;
            cell2.style.fontSize = "10px";
            cell2.style.wordBreak = "break-all";
            row.appendChild(cell1);
            row.appendChild(cell2);
            tbl.appendChild(row);
          }
      }

      var column_data_for_muliple = document.getElementById(el.eid + 'column_data_for_muliple');
      if (column_data_for_muliple) {
        column_data_for_muliple.appendChild(tbl);
      }
    }

    for (let i = 0; i < other_alerts.length; i++) {
      if (document.getElementById("label" + other_alerts[i].eid)) {
        document.getElementById("label" + other_alerts[i].eid).style.background = "#f9bebd";
      }
    }

    if (document.getElementById("label" + alert.eid)) {
      document.getElementById("label" + alert.eid).style.background = "#f86c6b";
    }


  });


if (countNames(data) <= 0) {
  timeline.labelWidth(60);
}

var element = d3.select('#pf-timeline').append('div').datum(data.filter(function (eventGroup) {
  return eventGroup.display === true;
}));
timeline(element);


var coll = document.getElementsByClassName("collapsible");
var ii;

for (ii = 0; ii < coll.length; ii++) {
  coll[ii].addEventListener("click", function () {
    this.classList.toggle("active_1");
    if (0 === 0) {

      setTimeout(() => {
        element.datum(data.filter(function (eventGroup) {

          return eventGroup.display === true;
        }));
        timeline(element);

        $('[data-toggle="popover"]').popover({
          'container': '#pf-timeline',
          'placement': 'top'
        });
      }, 0)
    }
  });
}



$('#timeline-selectpicker').on('changed.bs.select', function (event, clickedIndex, newValue, oldValue) {
  data[clickedIndex].display = !data[clickedIndex].display;
  element.datum(data.filter(function (eventGroup) {

    return eventGroup.display === true;
  }));

  if (dataCopy.length > 0) {
    for (let k = 0; k < dataCopy.length; k++) {
      if (dataCopy[k].display) {
        dataCopy[k].display = data[k].display;
      } else {
        dataCopy[k].display = false;
      }
    }
  }


  timeline(element);

  $('[data-toggle="popover"]').popover({
    'container': '#pf-timeline',
    'placement': 'top'
  });

});

var dataCopy = [];

setTimeout(() => {
  for (let i = 0; i < data.length; i++) {
    for (let j = 0; j < data[i].data.length; j++) {
      dataCopy.push({ name: data[i].name, data: data[i].data[j], action: data[i].data[j].action })
    }
  }


}, 1000);


let filtered_array = [];
let filtered = [];
function doneTyping() {
  filtered_array = [];
  let typing_value = document.getElementById('global-search').value.toUpperCase();

  if (typing_value === '') {
    let counter = 0;
    for (let i = 0; i < data.length; i++) {
      counter = 0;
      for (let k = 0; k < dataCopy.length; k++) {
        if (dataCopy[k].name === data[i].name) {
          if (counter === 0) {
            data[i].data = [];
            counter++;
          }
          data[i].data.push(dataCopy[k].data);
        }
      }
    }
  } else {
    //make the length of data to original length again start
    let counter = 0;
    for (let i = 0; i < data.length; i++) {
      counter = 0;
      for (let k = 0; k < dataCopy.length; k++) {
        if (dataCopy[k].name === data[i].name) {
          if (counter === 0) {
            data[i].data = [];
            counter++;
          }
          data[i].data.push(dataCopy[k].data);
        }
      }
    }
    //make the length of data to original length again end

    //filter for action
    // for (let i = 0; i < data.length; i++) {
    //   filtered = data[i].data.filter(item =>
    //     item["action"].includes(typing_value)
    //   );

    //   if (filtered.length > 0) {
    //     filtered_array.push({ "name": data[i].name, "data": filtered });
    //   }

    //   for (let a = 0; a < data.length; a++) {
    //     for (let b = 0; b < filtered_array.length; b++) {
    //       if (data[a].name === filtered_array[b].name) {
    //         data[a].data = filtered_array[b].data;
    //       } else {
    //         data[a].data = [];
    //       }
    //     }
    //   }
    // }

    //filter for action end


    //filter for eid

    // for (let i = 0; i < data.length; i++) {
    //   filtered = data[i].data.filter(item =>
    //     item["eid"].includes(typing_value)
    //   );

    //   if (filtered.length > 0) {
    //     filtered_array.push({ "name": data[i].name, "data": filtered });
    //   }

    //   for (let a = 0; a < data.length; a++) {
    //     for (let b = 0; b < filtered_array.length; b++) {
    //       if (data[a].name === filtered_array[b].name) {
    //         data[a].data = filtered_array[b].data;
    //       } else {
    //         data[a].data = [];
    //       }
    //     }
    //   }
    // }

    //filter for eid end


    //filter for pid

    for (let i = 0; i < data.length; i++) {
      filtered = data[i].data.filter(item => {
        for (let obj in item) {
          if (obj !== 'date') {
            if (item[obj].includes(typing_value)) {
              return item;
            }
          }
        }
      });
      if (filtered.length > 0) {
        filtered_array.push({ "name": data[i].name, "data": filtered });
      }
    }


    for (let a = 0; a < data.length; a++) {
      for (let b = 0; b < filtered_array.length; b++) {
        if (data[a].name === filtered_array[b].name) {
          data[a].data = filtered_array[b].data;
          break;
        } else {
          data[a].data = [];
        }
        // break;
      }
    }
    // }

    //filter for pid end


  }

  element.datum(data.filter(function (eventGroup) {
    return eventGroup.display === true;
  }));

  timeline(element);

  $('[data-toggle="popover"]').popover({
    'container': '#pf-timeline',
    'placement': 'top'
  });

}



setInterval(() => {
  let span_els = document.getElementsByClassName("dropdown-item");
  if (span_els.length > 0) {
    for (let i = 0; i < span_els.length; i++) {
      if (!(document.getElementsByClassName("dropdown-item")[i].lastElementChild.classList[0] === 'checkbox_add')) {
        let spanElement = document.createElement('span');
        spanElement.classList.add("checkbox_add");
        span_els[i].appendChild(spanElement);
      }
    }
  }
}, 0);


// var selectedActionArray = [];
let removedActionDataArray = [];
// var dataCopy = JSON.parse(JSON.stringify(data));


$('#timeline-selectpicker-action').on('changed.bs.select', function (event, clickedIndex, newValue, oldValue) {

  let filteredArray = removedActionDataArray.filter(x => x.action === actionList[clickedIndex]);
  let dataArrayIndex;
  if (filteredArray.length > 0) {
    for (let i = 0; i < data.length; i++) {
      if (data[i].name === filteredArray[0].name) {
        dataArrayIndex = i;
        break;
      }
    }
    for (let i = 0; i < filteredArray.length; i++) {
      data[dataArrayIndex].data.push(filteredArray[i].data);
    }
    for (let i = 0; i < removedActionDataArray.length; i++) {
      if (removedActionDataArray[i].action === filteredArray[0].action) {
        removedActionDataArray.splice(i, 1)
      }
    }
  }

  if (filteredArray.length === 0) {
    for (let d = 0; d < data.length; d++) {
      for (let e = 0; e < data[d].data.length; e++) {
        if (data[d].data[e].action === actionList[clickedIndex]) {
          removedActionDataArray.push({ name: data[d].name, data: data[d].data[e], action: data[d].data[e].action });
          data[d].data.splice(e, 1);
          e--;
        }
      }
    }
  }

  element.datum(data.filter(function (eventGroup) {
    return eventGroup.display === true;
  }));

  timeline(element);

  $('[data-toggle="popover"]').popover({
    'container': '#pf-timeline',
    'placement': 'top'
  });
});


$(window).on('resize', function () {
  timeline(element);
  $('[data-toggle="popover"]').popover({
    'container': '#pf-timeline',
    'placement': 'top'
  });
});


// $('#datepicker').datepicker({
//   autoclose: true,
//   todayBtn: 'linked',
//   todayHighlight: true
// });
//
// $('#datepicker').datepicker('setDate', today);
//
// $('#datepicker').on('changeDate', zoomFilter);

$(document.body).on('click', '.dropdown-menu li', function (event) {
  var $target = $(event.currentTarget);
  $target.closest('.dropdown')
    .find('[data-bind="label"]').text($target.text())
    .end()
    .children('.dropdown-toggle').dropdown('toggle');

  zoomFilter();

  return false;
});

function countNames(data) {
  var count = 0;
  for (var i = 0; i < data.length; i++) {
    if (data[i].name !== undefined && data[i].name !== '') {
      count++;
    }
  }
  return count;
}

function zoomFilter() {
  // var range = $('#range-dropdown').find('[data-bind="label"]' ).text(),
  //     position = $('#position-dropdown').find('[data-bind="label"]' ).text(),
  //     // date = $('#datepicker').datepicker('getDate'),
  //     startDate,
  //     endDate;
  // switch (range) {
  //   case '1 hour':
  //     range = ONE_HOUR;
  //     break;

  //   case '1 day':
  //     range = ONE_DAY;
  //     break;

  //   case '1 week':
  //     range = ONE_WEEK;
  //     break;

  //   case '1 month':
  //     range = ONE_MONTH;
  //     break;
  //      case '1 sec':
  //     range = ONE_SEC;
  //     break;
  //            case '1 minute':
  //     range = ONE_MINUTE;
  //     break;
  // }
  // switch (position) {
  //   case 'centered on':
  //     startDate = new Date(date.getTime() - range/2);
  //     endDate = new Date(date.getTime() + range/2);
  //     break;

  //   case 'starting':
  //     startDate = date;
  //     endDate = new Date(date.getTime() + range);
  //     break;

  //   case 'ending':
  //     startDate =  new Date(date.getTime() - range);
  //     endDate = date;
  //     break;
  // }
  // timeline.Zoom.zoomFilter(startDate, endDate);
}

// $('#reset-button').click(function() {
//   timeline(element);
//   $('[data-toggle="popover"]').popover({
//     'container': '#pf-timeline',
//     'placement': 'top'
//   });
// });
