import { Component, OnInit } from '@angular/core';
import {CommonapiService} from './_services/commonapi.service';
import { first } from 'rxjs/operators';
import { Chart } from 'chart.js';
import 'chartjs-plugin-labels';
import swal from 'sweetalert';
import { msg } from '../dashboard/_helpers/common.msg';
import { CommonVariableService } from './../dashboard/_services/commonvariable.service';
import {moment} from "vis-timeline";
import { Router, ActivatedRoute, NavigationEnd, RoutesRecognized } from '@angular/router';
@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css','./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {

  public dashboardData: any;
  distribution:any;
  query:any;
  host:any;
  hostcolumn:any;
  categorycolumn:any;
  rulescolumn:any;

  alienvault_critical:any;
  alienvault_high:any;
  alienvault_medium:any;
  alienvault_low:any;
  alienvault_info:any;
  otx_counter:any;

  ibmxforce_critical:any;
  ibmxforce_high:any;
  ibmxforce_medium:any;
  ibmxforce_low:any;
  ibmxforce_info:any;
  ibm_counter:any;

  rule_critical:any;
  rule_high: any;
  rule_medium:any;
  rule_low:any;
  rule_info:any;
  rule_counter:any;
  placholder:any;

  virustotal_critical:any;
  virustotal_high:any;
  virustotal_medium:any;
  virustotal_low:any;
  virustotal_info:any;
  vt_counter:any;
  cpt_down:any;
  route: string;
  currentURL='';
  purge_duration:any;
  project_name=this.commonvariable.APP_NAME
  ProductNameER=this.commonvariable.ProductNameER

  windowsOnline:any;
  windowsOffline:any;
  windowsDisabled:any;
  ubuntuOnline:any;
  ubuntuOffline:any;
  ubuntuDisabled:any;
  darwinsOnline:any;
  darwinsOffline:any;
  darwinsDisabled:any;

  constructor(
    private commonapi: CommonapiService,
    private commonvariable: CommonVariableService,private router: Router,
  ) {
   }

  ngOnInit() {
    this.getHostsCount();
    this.draw_server_metrics();
    this.placholder = '';
    this.commonapi.Dashboard().pipe(first()).subscribe((res: any) => {
        this.dashboardData = res;
        console.log(this.dashboardData.data.alert_data.source);
        this.purge_duration = res.data.purge_duration;
        this.alienvault_critical = this.dashboardData.data.alert_data.source.alienvault.CRITICAL;
        this.alienvault_high = this.dashboardData.data.alert_data.source.alienvault.HIGH;
        this.alienvault_medium = this.dashboardData.data.alert_data.source.alienvault.MEDIUM;
        this.alienvault_low = this.dashboardData.data.alert_data.source.alienvault.LOW;
        this.alienvault_info = this.dashboardData.data.alert_data.source.alienvault.INFO;
        this.otx_counter = this.dashboardData.data.alert_data.source.alienvault.TOTAL;
        if(this.otx_counter !==''){
        $('.otx_counter_val').show();
        $('.otx_counter_val2').show();
        $('.otx_counter_val3').hide();
        }
        //IBM X-IBMxForce
        this.ibmxforce_critical = this.dashboardData.data.alert_data.source.ibmxforce.CRITICAL;
        this.ibmxforce_high = this.dashboardData.data.alert_data.source.ibmxforce.HIGH;
        this.ibmxforce_medium = this.dashboardData.data.alert_data.source.ibmxforce.MEDIUM;
        this.ibmxforce_low = this.dashboardData.data.alert_data.source.ibmxforce.LOW;
        this.ibmxforce_info = this.dashboardData.data.alert_data.source.ibmxforce.INFO;
        this.ibm_counter = this.dashboardData.data.alert_data.source.ibmxforce.TOTAL;
        if(this.ibm_counter !==''){
          $('.ibm_counter_val').show();
        $('.ibm_counter_val2').show();
        $('.ibm_counter_val3').hide();
        }
        //rules
        this.rule_critical = this.dashboardData.data.alert_data.source.rule.CRITICAL;
        this.rule_high = this.dashboardData.data.alert_data.source.rule.HIGH;
        this.rule_medium = this.dashboardData.data.alert_data.source.rule.MEDIUM;
        this.rule_low = this.dashboardData.data.alert_data.source.rule.LOW;
        this.rule_info = this.dashboardData.data.alert_data.source.rule.INFO;
        this.rule_counter = this.dashboardData.data.alert_data.source.rule.TOTAL;
        if(this.rule_counter !==''){
          $('.rule_counter_val').show();
        $('.rule_counter_val2').show();
        $('.rule_counter_val3').hide();
        }
        //virus virustotal_warning
        this.virustotal_critical = this.dashboardData.data.alert_data.source.virustotal.CRITICAL;
        this.virustotal_high = this.dashboardData.data.alert_data.source.virustotal.HIGH;
        this.virustotal_medium = this.dashboardData.data.alert_data.source.virustotal.MEDIUM;
        this.virustotal_low = this.dashboardData.data.alert_data.source.virustotal.LOW;
        this.virustotal_info = this.dashboardData.data.alert_data.source.virustotal.INFO;
        this.vt_counter = this.dashboardData.data.alert_data.source.virustotal.TOTAL;
        console.log(this.vt_counter);
        if(this.vt_counter !==''){
          $('.vt_counter_val').show();
        $('.vt_counter_val2').show();
        $('.vt_counter_val3').hide();
        }

        if(this.otx_counter>0)
        {
        localStorage.setItem('alerts_name','alienvault');
        }
        else if(this.ibm_counter>0)
        {
        localStorage.setItem('alerts_name','ibmxforce');
        }
        else if(this.rule_counter>0)
        {
        localStorage.setItem('alerts_name','rule');
        }
        else{
        localStorage.setItem('alerts_name','virustotal');
        }
        this.distribution = this.dashboardData.data.distribution_and_status.hosts_platform_count;
        let distributionval = this.distribution;

        this.query = this.dashboardData.data.distribution_and_status.query;
        let queryval = this.query;

        this.host = this.dashboardData.data.distribution_and_status.hosts_status_count;
        let hostval = this.host;

        this.rulescolumn = this.dashboardData.data.alert_data.top_five.rule;
        let rulescolumnval = this.rulescolumn;

        this.categorycolumn = this.dashboardData.data.alert_data.top_five.query;
        let categorycolumnval = this.categorycolumn;

        this. hostcolumn = this.dashboardData.data.alert_data.top_five.hosts;
        let hostcolumnval = this.hostcolumn;


// Start Platform distribution chart
var platform_distibution = []
var platform_distibution_count=[]
var backgrund_colour=[]
for(const i in distributionval){
   platform_distibution.push(distributionval[i].os_name)
   platform_distibution_count.push(distributionval[i].count)
   if(distributionval[i].os_name=="windows"){
     backgrund_colour.push('#2A6D7C')
   }else if(distributionval[i].os_name=="darwin"){
     backgrund_colour.push('#F79750')
   }else{
     backgrund_colour.push('#A2D9C5')
   }
}
if(platform_distibution_count.length==0){
   $(document.getElementById('no-data-platform-distribution-chart')).append("No data");
   $('.no-data-platform-distribution').show();
} var myChart = new Chart('pie-chart-platform-distribution-chart', {
      type: 'pie',
      data: {
          labels: platform_distibution,
          datasets: [{
              data: platform_distibution_count,
              backgroundColor: backgrund_colour
          }]
      },
      options: {
      responsive: false,
      maintainAspectRatio: false,
      plugins: {
        labels: {
          render: 'percentage',
          fontColor: 'white',
          overlap: false,
        }
      },
        legend: {
          display: true,
          position: 'right',
          onClick: null ,
          labels: {
            fontColor: '#333',
            usePointStyle:true
        }
        },
      }
  });
// End Start Platform distribution chart

// Start host status chart

var Host_status_data = []
var Host_status_data_count=[]
var backgrund_colour=[]
for(const i in hostval){
  if(i=="online"){
    if(hostval.online !==0){
  Host_status_data.push("online")
  Host_status_data_count.push(hostval[i])
  // backgrund_colour.push('green')
  backgrund_colour.push('#77bfb7')
}
  }else{
    if(hostval.offline !==0){
    Host_status_data.push("offline")
    Host_status_data_count.push(hostval[i])
    // backgrund_colour.push("#dc3912")
    backgrund_colour.push("#FF8080")
  }
  }
}
if(Host_status_data_count.length==0 ){
   $(document.getElementById('no-data-pie-Host-status-result-chart')).append("No data");
   $('.pie-chart-Host-status').show();
   $('.pie-chart-Host-canvas').hide();
}
// End host status chart
// Start top 5 alerted hosts
var top_5hosts = []
var top_5hosts_count=[]
for(const i in hostcolumnval){
  top_5hosts.push(hostcolumnval[i].host_name)
  top_5hosts_count.push(hostcolumnval[i].count)
}
if(top_5hosts_count.length==0){
   $(document.getElementById('no-data-bar-chart-top_5_alerted_hosts')).append("No data");
   $('.alerted_hosts').hide();
}
var myChart2 = new Chart('bar-chart-top_5_alerted_hosts', {
  type: 'bar',
  data: {
      labels:top_5hosts,
      datasets: [{
          data: top_5hosts_count,
          backgroundColor: [
                    "#2A6D7C",
                    "#A2D9C5",
                    "#F79750",
                    "#794F5D",
                    "#6EB8EC"
                ],
          barPercentage: 0.5,
          categoryPercentage: 1.0
      }]
  },
  options: {
    borderSkipped:'right',
    tooltips:{
      intersect : false,
      mode:'index'
      },
    maintainAspectRatio: false,
    legend: {
      display: false
    },
    plugins: {
      labels: {
        render: () => {}
      }
    },
    scales: {
      xAxes: [{
        barThickness: 30,
        gridLines: {
            offsetGridLines: true,
            display : false,
        },
        ticks: {
          callback: function(label, index, labels) {
            var res = label.substring(0,2)+"..";
            return res;
          },
          minRotation: 45
        }
    }],
    yAxes: [{
      ticks: {
          beginAtZero: true,
          display: false,
      },
      gridLines: {
        drawBorder: false,
    }
  }]
    },
  },

  });
// End top 5 alerted hosts
// Start top 5 alerted categories
var top_5_categories = []
var top_5_categories_count=[]
for(const i in categorycolumnval){
  top_5_categories.push(categorycolumnval[i].query_name)
  top_5_categories_count.push(categorycolumnval[i].count)
}
if(top_5_categories_count.length==0){
   $(document.getElementById('no-data-bar-chart-top_5_alerted_categries')).append("No data");
   $('.categories_data').hide();
}

var myChart3 = new Chart('bar-chart-top_5_alerted_categries', {
  type: 'bar',
  data: {
      labels:top_5_categories,
      datasets: [{
          data: top_5_categories_count,
          backgroundColor: [
                    "#2A6D7C",
                    "#A2D9C5",
                    "#F79750",
                    "#794F5D",
                    "#6EB8EC"
                ],
          barPercentage: 0.5,
      }]
  },

  options: {
    tooltips:{
      intersect : false,
      // mode:'index'
      },
    maintainAspectRatio: false,
    legend: {
      display: false
    },
    plugins: {
      labels: {
        render: () => {}
      }
    },
    scales: {
      xAxes: [{
        barThickness: 30,
        gridLines: {
            offsetGridLines: true,
            display : false,
        },
        ticks: {
          callback: function(label, index, labels) {
            var res = label.substring(0,2)+"..";
            return res;
          },
          minRotation: 45
        }
    }],
    yAxes: [{
      ticks: {
          beginAtZero: true,
          display: false,
      },
      gridLines: {
        drawBorder: false,
    }
  }]
    },
  },
  });
// End top 5 alerted categories
// Start top 5 alerted rules
var top_5_rules = []
var top_5_rules_count=[]
for(const i in rulescolumnval){
  top_5_rules.push(rulescolumnval[i].rule_name)
  top_5_rules_count.push(rulescolumnval[i].count)
}
if(top_5_rules_count.length==0){
   $(document.getElementById('no-data-bar-chart-top_5_alerted_rules')).append("No data");
   $('.top_rules').hide();
}

var myChart4 = new Chart('bar-chart-top_5_alerted_rules', {
  type: 'bar',
  data: {
      labels:top_5_rules,
      datasets: [{
          data: top_5_rules_count,
          backgroundColor: [
                    "#2A6D7C",
                    "#A2D9C5",
                    "#F79750",
                    "#794F5D",
                    "#6EB8EC"
                ],
          barPercentage: 0.5,
      }]
  },
  options: {
    tooltips:{
      intersect : false,
      mode:'index'
      },
      responsive: true,
    maintainAspectRatio: false,
    legend: {
      display: false
    },
    plugins: {
      labels: {
        render: () => {}
      }
    },
    scales: {
      offset:false,
      xAxes: [{
        barThickness: 30,
        gridLines: {
            offsetGridLines: true,
            display : false,
        },
        ticks: {
          callback: function(label, index, labels) {
            var res = label.substring(0,2)+"..";
            return res;
          },
          minRotation: 45
        }
    }],
    yAxes: [{
      ticks: {
          beginAtZero: true,
          display: false,
      },
      gridLines: {
        drawBorder: false,
    }
  }]
    },
  },
  });
},
// error => {
//     this.failuremsg(msg.failuremsg);
// }
    );
  }
format_date(d){
  const format1 = "YYYY-MM-DD HH:mm:ss";
  return  moment(d).format(format1);

}
 draw_server_metrics(){
  var  current_date=new Date();
   var offset= new Date().getTimezoneOffset()* 60000;


    var start_time=new Date(current_date.getTime()+offset);
    var end_time=new Date(current_date.getTime()+offset);
   start_time.setHours(start_time.getHours() - 3);
   start_time.setMinutes(0);
   start_time.setSeconds(0);


   end_time.setHours(end_time.getHours() +1);
   end_time.setMinutes(0);
   end_time.setSeconds(0);

   var labels=[this.format_date(end_time)];
  var label_date=new Date(end_time);

   while(label_date.getTime()>start_time.getTime()){
     label_date.setHours(label_date.getHours()-1);
     labels.push(this.format_date(label_date));

   }
   console.log(labels);
   this.commonapi.get_server_metrics({"from_time":this.format_date(start_time)}).pipe(first()).subscribe((res: any) => {
     console.log(res);
     var disk_usage_data=res.data.DISKUSAGE;
     var rabbitmq_data=res.data.RABBITMQ;
     var nginx_data=res.data.NGINX;
     var top_hosts_generating_data=res.data.TOPHOSTS;
     var disk_usage_graph_data=[];
     var rabbitmq_graph_data=[];
     var non_success_requests_graph_data=[];
     var avg_bytes_graph_data=[];
     var top5_hosts_graph_data=[];

     disk_usage_graph_data = [disk_usage_data.free,(disk_usage_data.total-disk_usage_data.free).toFixed(2)];




     for(var data of rabbitmq_data ){
       rabbitmq_graph_data.push({
         t:data.created_at,
         y:data.value.queue_totals.messages

       });

     }

     var success_requests_graph_data=[];
     for(var data of nginx_data ){
       non_success_requests_graph_data.push({
         t:data.created_at,
         y:data.value.failure_count

       });
       success_requests_graph_data.push({
         t:data.created_at,
         y:data.value.success_count

       });

       avg_bytes_graph_data.push({
         t:data.created_at,
         y:data.value.total_size

       });

     }

var top_5hosts_label=[];
     for(var data of top_hosts_generating_data ){
       top5_hosts_graph_data.push({
         t:data.hostname,
         y:data.value

       });
       top_5hosts_label.push(data.hostname);

     }


     if(top5_hosts_graph_data.length==0){
      $(document.getElementById('no-data-bar-chart-top_5_hosts')).append("No data");
      $('.bar-graph-top5-hosts').hide();
    }
     var top5_hosts= new Chart('top5_hosts_data_graph', {
       type: 'bar',
       data: {
         labels:top_5hosts_label,
         datasets: [{
           data: top5_hosts_graph_data,
           backgroundColor: [
             "#2A6D7C",
             "#A2D9C5",
             "#F79750",
             "#794F5D",
             "#6EB8EC"
           ],
           barPercentage: 0.5,
           categoryPercentage: 1.0
         }]
       },
       options: {

         borderSkipped:'right',
         tooltips:{
           intersect : false,
           mode:'index',
           callbacks: {
             label: (item) => `${item.yLabel} events`,
           }
         },
         maintainAspectRatio: false,
         legend: {
           display: false
         },
         plugins: {
           labels: {
             render: () => {}
           }
         },
         scales: {
           xAxes: [{
             barThickness: 30,
             gridLines: {
               offsetGridLines: true,
               display : false,
             },
             ticks: {
               callback: function(label, index, labels) {
                 var res = label.substring(0,2)+"..";
                 return res;
               },
               minRotation: 45
             }
           }],
           yAxes: [{
             ticks: {
               beginAtZero: true,
               display: false,
               precision:0
             },
             gridLines: {
               drawBorder: false,
             },
            //  scaleLabel: {
            //    display: true,
            //    labelString: 'Count'
            //  }
           }]
         },
       },

     });
console.log(avg_bytes_graph_data);

  var date_rate_graph= new Chart('date_rate_graph', {
     type: 'line',
     data: {
       labels: labels,
       datasets: [{
         data: avg_bytes_graph_data,
         fill: false,
         borderColor: "rgb(110, 191, 182)",
         lineTension: 0.1
       }]
     },
     options: {
       tooltips: {
         callbacks: {
           label: (item) => `${item.yLabel} bytes`,
         },
       },
         legend: {
           display: false
       },
       scales: {
         xAxes: [{
           type: 'time',
           time: {
             unit: 'hour'
           }
         }],
         yAxes: [{
           ticks: {
             beginAtZero:true,
             precision:0
           }, scaleLabel: {
             display: true,
             labelString: 'Value(in bytes)'
           }
         }]
       }
     }
   });


   if(disk_usage_graph_data.length==0){
    $(document.getElementById('no-data-pie-Host-status-result-chart')).append("No data");
    $('.pie-chart-Host-canvas').hide();
  }
     var myChart1 = new Chart('disk_usage-pie-chart', {
       type: 'pie',
       data: {
         labels: ["Free","Used"],
         datasets: [{
           data: disk_usage_graph_data,
           backgroundColor: ["rgb(110, 191, 182)","#FF8080"]

         }]
       },
       options: {
         responsive: false,
         maintainAspectRatio: false,
         plugins: {
           labels: {
             render: 'percentage',
             fontColor: 'white',
             overlap: false,
           }
         },
         legend: {
           display: true,
           position: 'right',
           onClick: null ,
           labels: {
             fontColor: '#333',
             usePointStyle:true
           }
         },
       }
     });
    var non_success_requests_graph= new Chart('non_success_requests_graph', {
       type: 'line',
       data: {
         labels: labels,
         datasets: [ {
           label: 'Success ',
           data: success_requests_graph_data,
           borderColor: "rgb(110, 191, 182)",
           backgroundColor: "rgb(110, 191, 182)",
           fill: false,
           hidden: true,
         },
           {
             label: 'Failure',
             data: non_success_requests_graph_data,
             borderColor: "#FF8080",
             fill: false,
             backgroundColor: "#FF8080",
           }],
       },
       options: {
        legend: {
          display: true
        },
         scales: {
           xAxes: [{
             type: 'time',
             time: {
               unit: 'hour'
             }
           }],
           yAxes: [{
             ticks: {
               beginAtZero:true,
               precision:0
             }, scaleLabel: {
               display: true,
               labelString: 'Count'
             }
           }]
         }
       }
     });
     var rabbitmq_pending_tasks= new Chart('pending_rabbitmq_tasks_graph', {
       type: 'line',
       data: {
         labels: labels,
         datasets: [{
           data: rabbitmq_graph_data,
           fill: false,
           borderColor: "rgb(110, 191, 182)",
           lineTension: 0.1
         }]
       },
       options: {
         legend: {
           display: false
         },
         scales: {
           xAxes: [{
             type: 'time',
             time: {
               unit: 'hour'
             }
           }],
           yAxes: [{
             ticks: {
               beginAtZero:true,
               precision:0
             }, scaleLabel: {
               display: true,
               labelString: 'Count'
             }
           }]
         }
       }
     });

   });

  }

  downloadFile(e,val){
    this.currentURL = window.location.href;
    let toArray = this.currentURL.split(':');
    this.cpt_down = window.location.origin + "/downloads/" + val;
    window.open(this.cpt_down);
    }

    failuremsg(msg){
      swal({
        icon: "warning",
        text: msg,
        buttons: {
          cancel: {
            text: "Close",
            value: null,
            visible: true,
            closeModal: true,
          },
        },
      })
    }

    closeModal(modalId){
      let modal = document.getElementById(modalId);
      modal.style.display = "none";
      $('.modal-backdrop').remove();
    }
    goToAlerts(value,alertType) {
      this.router.navigate(['/alerts'],{queryParams: { 'id': '', 'from':value,'alertType':alertType }});
    }

    getHostsCount(){
      this.commonapi.Hosts_count().subscribe((res:any) => {
        this.windowsOnline = res.data.windows.online;
        this.windowsOffline = res.data.windows.offline;
        this.windowsDisabled = res.data.windows.removed;
        if(this.windowsOnline !=='' || this.windowsOnline !==''){
          $('.window_widget_body').show();
          $('.window_widget_body2').hide();
        }
        this.ubuntuOnline = res.data.linux.online;
        this.ubuntuOffline = res.data.linux.offline;
        this.ubuntuDisabled = res.data.linux.removed;
        if(this.ubuntuOnline !=='' || this.ubuntuOffline !==''){
          $('.linux_widget_body').show();
          $('.linux_widget_body2').hide();
        }
        this.darwinsOnline = res.data.darwin.online;
        this.darwinsOffline = res.data.darwin.offline;
        this.darwinsDisabled = res.data.darwin.removed;
        if(this.darwinsOnline !=='' || this.darwinsOffline !==''){
          $('.apple_widget_body').show();
        $('.apple_widget_body2').hide();
        }
    });
    }
}
