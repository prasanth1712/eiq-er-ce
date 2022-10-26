import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { Subject } from 'rxjs';
import { Router, ActivatedRoute } from '@angular/router';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../../dashboard/_services/commonvariable.service';
// import { DataTablesModule } from 'angular-datatables';
import { DataTableDirective } from 'angular-datatables';
import { environment } from '../../../../environments/environment';
import { Location } from '@angular/common';
import { saveAs } from 'file-saver';
import { Title } from '@angular/platform-browser';
declare let d3: any;
declare var alerted_entry: any;
declare var $: any;
var PaginationIndex
var TempIndex
var NextDataId
var SelectedNodeID

class activitydatanode {
  columns: string;
}

class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}

@Component({
  selector: 'app-activity',
  templateUrl: './activity.component.html',
  styleUrls: ['./activity.component.css']
})

export class ActivityComponent implements AfterViewInit, OnDestroy, OnInit {
  myjson: any = JSON;
  sub: any;
  id: any;
  activitydata: any;
  nodes: any;
  nodesdata: any;
  activitynode: any;
  nodekey: any;
  activitycount: any;
  activitysearch:any;
  errorMessage:any;
  searchText: any;
  userData: any;
  countresult: any;
  temp_var: any;
  recentactivitydata: any;
  activitydatanode: any;
  recentactivitycount: any;
  groupList: any = [];
  p: number = 1;
  term: any;
  activity_name: any;
  public data = {};
  defaultData: boolean;
  queryname: any;
  test: any;
  activityname: any;
  nodesdata_name: any;
  selectedItem: any;
  host_identifier: any;
  export_csv_data: any = {}
  query_name: any;
  click_queryname:any;
  @ViewChild(DataTableDirective)
  dtElement: DataTableDirective;
  dtOptions: any = {};
  dtTrigger: Subject<any> = new Subject();
  Events_dropdownList = [];
  Events_selectedItems = [];
  Events_dropdownSettings = {};
  PreviousDataIds={}
  constructor(
    private _Activatedroute: ActivatedRoute,
    private commonapi: CommonapiService,
    private commonvariable: CommonVariableService,
    private http: HttpClient,
    private _location: Location,
    private titleService: Title,
    private router: Router,

  ) { }

  ngOnInit(): void {

    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Hosts");
    // localStorage.removeItem('activity_nodekey');
    this.sub = this._Activatedroute.paramMap.subscribe(params => {
      this.getFromActivityData();

      this.id = params.get('id');
      // alert(this.id)
     this.commonapi.host_name_api(this.id).subscribe(res => {
        this.activitydata = res;
        if(this.activitydata.status == "failure"){
          this.pagenotfound();
        }
        else{
        this.host_identifier = this.activitydata.data.host_identifier


        // this.nodekey = this.activitydata.data.node_key;
        if (this.activitydata.data.id == this.id) {
          this.nodes = this.activitydata.data.node_info.computer_name;
        }
      }
      });

      this.commonapi.recent_activity_count_api(this.id).subscribe(res => {
        this.nodesdata = res;

        this.activitynode = this.nodesdata.data;
        this.click_queryname=this.activitynode[0].name
        this.query_name=this.activitynode[0].name;

        this.activitycount = Object.keys(this.activitynode).length;

        this.searchText;

        this.defaultData=true;
        this.getFromActivityData();
        this.Refresh_datatable()


      });


    });

    this.Events_dropdownSettings = {
      singleSelection: false,
      text:"Select Events",
      selectAllText:'Select All',
      unSelectAllText:'UnSelect All',
      enableSearchFilter: true,
      badgeShowLimit: 1,
      classes:"myclass custom-class",
    };
    this.Events_dropdownList = [
      {"id":1,"itemName":"File"},
      {"id":2,"itemName":"Process"},
      {"id":3,"itemName":"Remote Thread"},
      {"id":4,"itemName":"Process Open"},
      {"id":5,"itemName":"Removable Media"},
      {"id":6,"itemName":"Image Load"},
      {"id":7,"itemName":"Image Load Process Map"},
      {"id":8,"itemName":"HTTP"},
      {"id":9,"itemName":"SSL"},
      {"id":10,"itemName":"Socket"},
      {"id":11,"itemName":"DNS"},
      {"id":12,"itemName":"DNS Response"},
      {"id":13,"itemName":"Registry"},
      {"id":14,"itemName":"Yara"},
      {"id":15,"itemName":"Logger"},
      {"id":16,"itemName":"File Timestamp"},
      {"id":17,"itemName":"PeFile"},
      {"id":18,"itemName":"Defender Events"},
      {"id":19,"itemName":"Pipe Events"}
    ];
    // this.initialise_val()

  }

  pagenotfound() {
      this.router.navigate(['/pagenotfound']);
  }

  getFromActivityData() {
    var that=this;
    this.dtOptions = {
      pagingType: 'simple',
      pageLength: 10,
      scrollX: false,
      scrollY: 480,
      serverSide: true,
      processing: true,
      searching: true,
      dom: '<"pull-right"B><"pull-right"f><"pull-left"l>tip',
      buttons: [
        {
          text: 'CSV',
          buttonClass: 'btn-csv btn',
          attr:  {id: 'IdExport'},
          action: function ( e, dt, node, config ) {
            that.get_csv_data();
          },
        },
      ],
      "language": {
        "search": "Search: ",
        "paginate": {
          "previous": '<i class="fas fa-angle-double-left"></i> Previous',
          "next": 'Next <i class="fas fa-angle-double-right"></i>',
        },
        "lengthMenu": "<ng-container class=custom-pagination-length>Results per page: _MENU_</ng-container>",
      },
      ajax: (dataTablesParameters: any, callback) => {
        $('.recentActivityLoader').show();
        let node_id = this.id;
        var body = dataTablesParameters;
        PaginationIndex=body['start']
        if(PaginationIndex>TempIndex)   //checking next page index
        {
          body['start']=NextDataId
        }
        else if (PaginationIndex<TempIndex)  //checking Previous page index
        {
          body['start']=this.PreviousDataIds[PaginationIndex]
        }
        else if(PaginationIndex == TempIndex){
          body['start']= SelectedNodeID
        }
        SelectedNodeID = body['start'];
        TempIndex=PaginationIndex;
        body['limit'] = body['length'];
        body['node_id'] = node_id;
        if (!this.query_name && !this.queryname){
          return;
        }
        if (this.defaultData) {
          body['query_name'] = this.query_name;
          this.selectedItem = this.query_name;
          this.queryname = this.query_name;

        } else {
          body['query_name'] = this.queryname;
        }
        if(body.search.value!= ""  &&  body.search.value.length>=1)
        {
          body['searchterm']=body.search.value;
        }
        if(body['searchterm']==undefined){
          body['searchterm']="";
        }
        if(this.Events_selectedItems.length>0){
          var eventids=''
          for(const eventid in this.Events_selectedItems){
            eventids=eventids + ',' + this.Events_selectedItems[eventid].id
          }
          body["column_name"]="eventid",
          body["column_value"]=eventids
        }
        this.http.post<DataTablesResponse>(environment.api_url + "/hosts/recent_activity", body, {headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res => {
          $('.recentActivityLoader').hide();
          this.recentactivitydata = res;
          this.activitydatanode = this.recentactivitydata.data.results;
          for(const id in this.activitynode){
            if(this.activitynode[id].name==this.queryname){
              this.activitynode[id].count=res.data['total_count']
            }
          }
          for (var v = 0; v < this.activitydatanode.length; v++) {
            if (this.activitydatanode[v].columns != '') {
              this.activitydatanode[v].columns = this.activitydatanode[v].columns;
            }


          }
          if(this.activitydatanode.length >0 &&  this.activitydatanode!=undefined)
            {
              this.PreviousDataIds[PaginationIndex]=(this.activitydatanode[0].id)+1
              NextDataId=(this.activitydatanode[this.activitydatanode.length - 1]).id
              $('.dataTables_paginate').show();
              $('.dataTables_info').show();
            }
            else{
              this.activitydatanode=null;
              if(body.search.value=="" || body.search.value == undefined)
              {
                this.errorMessage="No Data Found";
              }
              else{
                this.errorMessage="No Matching Record Found";
              }

              $('.dataTables_paginate').hide();
              $('.dataTables_info').hide();

            }
          // this.temp_var=true;
          callback({
            recordsTotal: this.recentactivitydata.data.categorized_count,
            recordsFiltered: this.recentactivitydata.data.count,

            data: []
          });
        });
      },
      ordering: false,
      columns: [{ data: 'columns' }],
    };
    $(document).on( 'click', '.paginate_button', function (e) {
      if(!(e.currentTarget.className).includes('disabled')){
          $('.paginate_button.next').addClass('disabled');
          $('.paginate_button.previous').addClass('disabled');
      }})
  }
  action(event): void {
    event.stopPropagation();
  }
  ngAfterViewInit(): void {
    this.dtTrigger.next();
  }

  ngOnDestroy(): void {
    this.dtTrigger.unsubscribe();
  }

  getByActivityId(event, newValue, qryname, node_id): void {
  this.Events_selectedItems=[]
   if(this.click_queryname==qryname){
   }else{
    this.selectedItem = newValue;
    this.queryname = qryname;
    this.defaultData = false;
    this.Refresh_datatable()
    this.click_queryname=qryname;
  }
    this.PreviousDataIds={}
    NextDataId=0
  }
  get_csv_data() {
    this.export_csv_data["host_identifier"] = this.host_identifier;
    this.export_csv_data["query_name"] = this.queryname;
    if(this.Events_selectedItems.length>0){
      var eventids=''
      for(const eventid in this.Events_selectedItems){
        eventids=eventids + ',' + this.Events_selectedItems[eventid].id
      }
      this.export_csv_data["column_name"]="eventid",
      this.export_csv_data["column_value"]=eventids
    }
    this.commonapi.recent_activity_search_csv_export(this.export_csv_data).subscribe(blob => {
      saveAs(blob, this.queryname+"_"+this.host_identifier+'.csv');

    })
  }


  goBack() {
    this._location.back();
  }
  initialise_val(eventdata,data_process_guid) {

    const menuItems = [
      {
        title: 'Show More',
        action: (elm, d, i) => {

          if (d.count >= 20) {
            call_more(d);

          }
          // TODO: add any action you want to perform
        }
      }
    ];
    d3.contextMenu = function (menu, openCallback) {
      // create the div element that will hold the context menu
      d3.selectAll('.d3-context-menu').data([1])
        .enter()
        .append('div')
        .attr('class', 'd3-context-menu');

      // close menu
      d3.select('body').on('click.d3-context-menu', function () {
        d3.select('.d3-context-menu').style('display', 'none');
      });

      // this gets executed when a contextmenu event occurs
      return function (data, index) {
        if (!(data.node_type=='action' && data.count>20)){
          return;
        }
        var elm = this;

        d3.selectAll('.d3-context-menu').html('');
        var list = d3.selectAll('.d3-context-menu').append('ul');
        list.selectAll('li').data(menu).enter()
          .append('li')
          .html(function (d) {
            return (typeof d.title === 'string') ? d.title : d.title(data);
          })
          .on('click', function (d, i) {
            d.action(elm, data, index);
            d3.select('.d3-context-menu').style('display', 'none');
          });

        // the openCallback allows an action to fire before the menu is displayed
        // an example usage would be closing a tooltip
        if (openCallback) {
          if (openCallback(data, index) === false) {
            return;
          }
        }

        // display context menu
        d3.select('.d3-context-menu')
          .style('left', (d3.event.pageX - 2) + 'px')
          .style('top', (d3.event.pageY - 2) + 'px')
          .style('display', 'block');

        d3.event.preventDefault();
        d3.event.stopPropagation();
      };
    };
    var token_value = localStorage.getItem('token');
    var eid = eventdata.columns.eid;

    var jsonObjectOfActions = {
      "FILE_": "target_path",
      "PROC_": "path",
      "HTTP_": "remote_address",
      "SOCKET_": "remote_address",
      "IMAGE_": "image_path",
      "TLS_": "issuer_name",
      "REG_":"target_name",
      "DNS_":"domain_name"
    }

    var margin = {top: 20, right: 120, bottom: 20, left: 120},
      width = 960 - margin.right - margin.left,
      height = 800 - margin.top - margin.bottom;

    var i = 0,
      duration = 750;

    var tree = d3.layout.tree()
      .size([height, width]);
    var diagonal = function link(d) {
      return "M" + d.source.y + "," + d.source.x
        + "C" + (d.source.y + d.target.y) / 2 + "," + d.source.x
        + " " + (d.source.y + d.target.y) / 2 + "," + d.target.x
        + " " + d.target.y + "," + d.target.x;
    };

    var root;
    var id = this.id;
    var svg = d3.select("#d3-graph-2").append("svg")
      .attr("width", width + margin.right + margin.left)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    var alert_process_guid;
    if (eventdata.columns.action == 'PROC_TERMINATE') {
      alert_process_guid = data_process_guid;
    } else {
      alert_process_guid = data_process_guid;
    }
    let ajaxAlertData = {
        "process_guid":alert_process_guid,
        "node_id":this.id,

    }
    $.ajax({
      type: "POST", //rest Type
      dataType: 'json', //mispelled
      url: environment.api_url + "/alerts/process",
      async: false,
      headers: {
        "content-type": "application/json",
        "x-access-token": token_value
      },
      data: JSON.stringify(ajaxAlertData),
      success: function (msgdata) {
        var name=data_process_guid;
        var data={};
        var event_data=eventdata.columns;
        if(event_data.hasOwnProperty('parent_process_guid')&&event_data['parent_process_guid']==data_process_guid){
          name=event_data['parent_path'];
          data['process_guid']=data_process_guid;
          data['path']=name;
        }
        else if(event_data.hasOwnProperty('process_guid')&&event_data['process_guid']==data_process_guid){
          if(!event_data.hasOwnProperty('parent_process_guid')){
            name=event_data['process_name'];
            data['process_guid']=data_process_guid;
            data['process_name']=name;

          }else{
            name=event_data['path'];
            data=event_data;
          }
        }
        root = msgdata.data;
        root['data']=data;
        root['name']=name;
        root['path']=name;
        create_graph(root);
      }
    });

    function create_graph(root) {
      root.x0 = height / 2;
      root.y0 = 0;
      root.children = root.all_children;
      root.children.forEach(function (d) {
        if (!d.hasOwnProperty('children')) {
          collapse(d);
        }
        d.hidden = false;
      });
      root.hidden = false;
      update(root);
      blinkNode();
      d3.select(self.frameElement).style("height", "800px");
    }

    function update(source) {
      // Compute the new tree layout.
      var nodes = tree.nodes(root).filter(function (d) {
          return !d.hidden;
        }).reverse(),
        links = tree.links(nodes);

      // Normalize for fixed-depth.
      nodes.forEach(function (d) {
        d.y = d.depth * 180;
      });

      // Update the nodes…
      var node = svg.selectAll("g.node")
        .data(nodes, function (d) {
          return d.id || (d.id = ++i);
        });
      // Enter any new nodes at the parent's previous position.
      var nodeEnter = node.enter().append("g")
        .attr("class", function (d) {
          if (d.hasOwnProperty("data") && d.data.eid == eid) {
            return "node ";
          }
          return "node";
        })

        .attr("transform", function (d) {
          return "translate(" + source.y0 + "," + source.x0 + ")";
        })


        .on('click', function (d, i) {
          selectedNode(d);

          if ((d.node_type == 'action' || d.data.action == 'PROC_CREATE') && !d.hasOwnProperty("fetched")) {
            callChild(d);

          } else {
            click(d);
          }
        })
        .on('contextmenu', d3.contextMenu(menuItems));


      nodeEnter.append("circle")
        .attr("r", 4.5)
        .style("fill", function (d) {

          if ((d.node_type == 'action' || d.hasOwnProperty("has_child")) && !d.hasOwnProperty("children") && !d.hasOwnProperty("_children") && !d.hasOwnProperty("all_children")) {
            d._children = [];


            return "lightsteelblue";
          } else {
            return d._children ? "lightsteelblue" : "#fff";
          }
        });

      nodeEnter.append("text")
        .attr("x", function (d) {
          return d.children || d._children ? -10 : 10;
        })
        .attr("dy", ".35em")
        .attr("text-anchor", function (d) {
          return d.children || d._children ? "end" : "start";
        })
        .text(function (d) {
          return getTitle(d)
        })
        .style("fill-opacity", 1e-6);


      nodeEnter.append("title")
        .text(function (d) {
          getTitle(d);
        });
      // Transition nodes to their new position.
      var nodeUpdate = node.transition()
        .duration(duration)
        .attr("transform", function (d) {
          return "translate(" + d.y + "," + d.x + ")";
        });

      nodeUpdate.select("circle")
        .attr("r", 4.5)
        .style("fill", function (d) {
          return d._children ? "lightsteelblue" : "#fff";
        });

      nodeUpdate.select("text")
        .style("fill-opacity", 1);

      // Transition exiting nodes to the parent's new position.
      var nodeExit = node.exit().transition()
        .duration(duration)
        .attr("transform", function (d) {
          return "translate(" + source.y + "," + source.x + ")";
        })
        .remove();

      nodeExit.select("circle")
        .attr("r", 4.5);

      nodeExit.select("text")
        .style("fill-opacity", 1e-6);

      // Update the links…
      var link = svg.selectAll("path.link")
        .data(links, function (d) {
          return d.target.id;
        });

      // Enter any new links at the parent's previous position.
      link.enter().insert("path", "g")
        .attr("class", "link")
        .attr("d", function (d) {

          var o = {x: source.x0, y: source.y0};
          return diagonal({source: o, target: o});
        }).attr("stroke", function (d) {
        return linkColor(d.target);
      });

      // Transition links to their new position.
      link.transition()
        .duration(duration)
        .attr("d", diagonal);

      // Transition exiting nodes to the parent's new position.
      link.exit().transition()
        .duration(duration)
        .attr("d", function (d) {
          var o = {x: source.x, y: source.y};
          return diagonal({source: o, target: o});
        })
        .remove();

      // Stash the old positions for transition.
      nodes.forEach(function (d) {
        d.x0 = d.x;
        d.y0 = d.y;
      });
      // node.on('contextmenu', d3.contextMenu(menuItems));
    }

    function click(d) {
      if (d.children) {
        d._children = d.children;
        d.children = null;
        if (d._children) {
          d._children.forEach(function (n) {
            n.hidden = true;
          });
          if (d.parent) {
            d.parent.children = d.parent.all_children;
            d.parent.children.forEach(function (n) {
              n.hidden = false;
            });
          }
        }
      } else {
        d.children = d._children;
        d._children = null;
        if (d.children) {
          d.children.forEach(function (n) {
            n.hidden = false;
          });

          if (d.parent) {
            d.parent.children = [d,];
            d.parent.children.filter(function (n) {
              return n !== d;
            }).forEach(function (n) {
              n.hidden = true;
            });
          }
        }
      }
      update(d);
    }

    function collapse(d) {
      if (d.children) {
        d.all_children = d.children;
        d._children = d.children;
        d._children.forEach(collapse);
        d.children = null;
        d.hidden = true;
      }
    }

    function blinkNode() {
      setInterval(function () {
        $('.blink-node').fadeTo('slow', 0.1).fadeTo('slow', 5.0);
      }, 1000);


    }

    function linkColor(link) {

      var action_colors = {
        "DNS_RESPONSE": "#fd7e14",
        "DNS_": "#007bff",
        "FILE_": "#dc3545",
        "PROC_": "#ffc107",
        "SOCKET_": "#28a745",
        "HTTP_": "#6c757d",
        "REG_": "#0000FF",
        "TLS_": "#20c997",
        "IMAGE_": "#7F007F",
      }
      for (var jsonObject in jsonObjectOfActions) {
        if (link.data && 'action' in link.data && link.data.action.includes(jsonObject)&& action_colors.hasOwnProperty(jsonObject)) {
          return action_colors[jsonObject];
        } else {
          if (link.node_type == 'action' && 'action' in link && link.action.includes(jsonObject) && action_colors.hasOwnProperty(jsonObject)) {
            return action_colors[jsonObject];
          }
        }
      }
      return "#0000FF";

    }

    function getTitle(d) {
      var name = d.name;
      if (d.node_type != 'action') {
        for (var jsonObject in jsonObjectOfActions) {
          if (d.data && 'action' in d.data && d.data.action.includes(jsonObject)) {
            let tempValue = jsonObjectOfActions[jsonObject];

            name = d.data[tempValue];
            if (d.data.action.includes("SOCKET")) {
              name = name + ":" + d.data.remote_port;
            }
            break;
          }
        }
      } else {
        name = name + "(" + d.count + ")";
      }
      if (name) {
        var lastlength = name.lastIndexOf('\\');
        var filter_process_name = name.substring(lastlength + 1);
        if (filter_process_name==''){
          var url = name.split( '\\' );
          if(url.length>=2){
           filter_process_name = url[ url.length - 2 ] ;
          }
        }
      }
      return filter_process_name;
    }

    function callChild(d) {

      if (d.hasOwnProperty("fetched") || d.hasOwnProperty("fetching")) {
        return
      }
      call_more(d);


    }

    function call_more(d) {
      d.fetching=true;
      if ((d.process_guid) && (d.node_type === 'action')) {

        let token_val = localStorage.getItem('token');
        let url_get_events_by_action_and_pgid = environment.api_url + '/alerts/process/child';
        let child_ajaxData = {
          "process_guid": d.process_guid,
          "action": d.action,
          "last_time": d.last_time,
          "node_id":id,
        }

        get_events_by_action_and_pgid();

        function get_events_by_action_and_pgid() {
          $.ajax({
            url: url_get_events_by_action_and_pgid,
            contentType: "application/json",
            headers: {
              "content-type": "application/json",
              "x-access-token": token_val
            },
            data: JSON.stringify(child_ajaxData),
            dataType: "json",
            type: "POST"
          }).done(function (data, textStatus, jqXHR) {
            delete d.fetching;
            d.fetched = true;
            d.last_time = data.data.last_time;
            if (data && data.data.child_data.length > 0)
              hideParentChild(d, data.data.child_data);
          }) .fail(function (jqXHR, exception) {
            delete d.fetching;
          })
        }
      } else {
        if (d.data.action === 'PROC_CREATE' && d.node_type!='root') {
          var url = window.location.pathname;

          token_value = localStorage.getItem('token');
          let url_get_events_by_pgid = environment.api_url + '/alerts/process';
          let ajaxData = {
            "process_guid": d.data.process_guid,
            "node_id":id
          }

          get_events_by_pgid();

          function get_events_by_pgid() {
            $.ajax({
              url: url_get_events_by_pgid,
              contentType: "application/json",
              headers: {
                "content-type": "application/json",
                "x-access-token": token_value
              },
              data: JSON.stringify(ajaxData),
              dataType: "json",
              type: "POST"
            }).done(function (data, textStatus, jqXHR) {

              d.fetched = true;
              delete d.fetching;
              if (data && data.data.all_children.length > 0)
                hideParentChild(d, data.data.all_children);

            })  .fail(function (jqXHR, exception) {
              delete d.fetching;

            })
          }

        }

      }
    }

    function hideParentChild(d, data) {

      d.children = null;
      if (d.all_children) {
        Array.prototype.push.apply(d.all_children, data)

      } else {
        d.all_children = data;

      }
      d._children = d.all_children;
      click(d);
    }


    var coll2 = document.getElementsByClassName("collapsible2");
    var n;

    for (n = 0; n < coll2.length; n++) {
      coll2[n].addEventListener("click", function () {
        this.classList.toggle("active_1");
      });
    }

    function selectedNode(info) {
      let el = info.data;
      var eventsData_process = document.getElementById('eventsData_process');
      // if (eventsData_process) {
      while (eventsData_process.firstChild) eventsData_process.removeChild(eventsData_process.firstChild);
      // }


      if (el) {

        // delete el.utc_time;
        // delete el.time;
        // delete el.process_guid;

        // for (let i=0; i < el.events.length; i++){

        var TableRow = '';
        var title=el.eid;
        if(title==undefined){
          title=el.process_guid;
        }
        TableRow +=
          '<div class="card" style="margin-bottom: 0.2rem;">' + '<div class="card-header" id="label_2' + title + '">' +
          '<h5 class="mb-0" style="">' + '<button class="btn" data-toggle="collapse"  aria-expanded="false">'
          + title
          + '</button>'
          + '</h5>'
          + '</div>'
          + '<div class="collapse show">'
          + '<div class="card-body">'
          + '<div id ="' + el.action + 'column_data">'
          + '</div>'
          + '</div>'
          + '</div>'
          + '</div>';
        TableRow += '';

        $('#eventsData_process').append(TableRow);
        var tbl = document.createElement("table");
        tbl.setAttribute("class", "table table-striped- table-bordered table-hover table-checkable");
        tbl.setAttribute("style", "margin-bottom: 0rem;");
        for (let child in el) {
          var row = document.createElement("tr");
          var cell1 = document.createElement("td");
          var cell2 = document.createElement("td");
          var firstCellText = document.createTextNode(child);
          var secondCellText = document.createTextNode(el[child]);
          cell1.appendChild(firstCellText);
          cell1.style.fontSize = "11px";
          cell1.style.fontWeight = '600';
          // cell1.style.fontFamily = "Roboto";
          // cell1.style.color = '#212529';
          cell1.style.wordBreak = "break-all";
          cell1.style.minWidth = "75px"
          cell1.appendChild(secondCellText);
          cell2.style.fontSize = "10px";
          cell2.style.fontWeight = '500';
          // cell2.style.fontFamily = "Roboto";
          // cell2.style.color = '#212529';
          cell2.style.wordBreak = "break-all";
          var data = el[child];
          var is_hyperlink = false;
          var domain_md5_link;
          if (child === 'domain_name') {
            domain_md5_link = "https://www.virustotal.com/#/domain/" + data.substring(1, data.length);
            is_hyperlink = true;
          } else if (child == 'md5') {
            domain_md5_link = "https://www.virustotal.com/#/file/" + data + "/detection";
            is_hyperlink = true;


          }
          if (is_hyperlink == true) {
            var atag = document.createElement("a");
            atag.target = "_blank";
            atag.style.color = "blue";
            atag.href = domain_md5_link;
            atag.appendChild(secondCellText);
            cell2.appendChild(atag);

          } else {
            cell2.appendChild(secondCellText);

          }

          // cell2.setAttribute("class", "cellCss");

          row.appendChild(cell1);
          row.appendChild(cell2);
          tbl.appendChild(row);
        }
        var column_data = document.getElementById(el.action + 'column_data');
        if (column_data) {
          column_data.appendChild(tbl);
        }

      } else {
        var TableRow = '';
        TableRow += '<h5 class="mb-0" style="text-align: center;font-size: 12px; color: #788093; margin-right: 65px; margin-top: 35px;">' + 'Click an event node to view information'
          + '</h5>'

        TableRow += '';
        $('#eventsData_process').append(TableRow);
        var tbl = document.createElement("table");
      }
    }

    selectedNode('info');
  }
  process_guid_graph(eventdata,process_guid){
    this.initialise_val(eventdata,process_guid);
    $('#processTree').modal('show');

  }
  close_data(){
document.getElementById("d3-graph-2").innerHTML = '';
  }
  Refresh_datatable(){
    this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
      dtInstance.destroy();
      this.dtTrigger.next();
    });
  }
  onItemSelect(item:any){
    this.Refresh_datatable()
  }
  OnItemDeSelect(item:any){
    this.Refresh_datatable()
  }
  onSelectAll(items: any){
    this.Refresh_datatable()
  }
  onDeSelectAll(items: any){
    this.Events_selectedItems=[]
    this.Refresh_datatable()
  }
}
