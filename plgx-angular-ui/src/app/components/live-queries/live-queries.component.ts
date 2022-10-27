import {Component, OnInit, ViewChild, OnDestroy,AfterViewInit} from '@angular/core';
import {FormGroup, FormBuilder} from "@angular/forms";
import swal from 'sweetalert';
import { Router, NavigationEnd } from '@angular/router';
import {CommonapiService} from '../../dashboard/_services/commonapi.service';
import { CommonVariableService } from '../../dashboard/_services/commonvariable.service';
import {ActivatedRoute} from '@angular/router';
import {NgxSpinnerService} from "ngx-spinner";
import {Subscription} from 'rxjs';
import {Title} from '@angular/platform-browser';

declare var $: any;
import 'datatables.net';

import {Subject} from 'rxjs';
import {HttpClient} from '@angular/common/http';
import {environment} from '../../../environments/environment'

import 'ace-builds/src-noconflict/mode-javascript';
import * as THEME from 'ace-builds/src-noconflict/theme-github';

import * as langTools from 'ace-builds/src-noconflict/ext-language_tools';
import {ToastrService} from "ngx-toastr";
import {Datatablecolumndefs} from '../../dashboard/_helpers/datatable-columndefs';
import Swal from 'sweetalert2';
let currentQueryID;
const tables = localStorage.getItem("Livequerytable");
const keywords = "select|from|where|and|or|group|by|order|limit|offset|having|as|case|when|else|end|type|left|right|join|on|outer|desc|asc|union|table|if|not|null|inner",
  builtinFunctions = "avg|count|first|last|max|min|sum|ucase|lcase|mid|len|round|rank|now|format|coalesce|ifnull|isnull|nvl",
  dataTypes = "int|numeric|decimal|date|varchar|char|bigint|float|double|bit|binary|text|set|timestamp|money|real|number|integer",
  all_columns = localStorage.getItem("Livequerycolumn");
var str = window.location.href;
str = str.substr(str.indexOf(':') + 3);
var socket_ip = str.substring(0, str.indexOf('/'));
var live_url = environment.socket_url;
if (live_url) {
  var socket_url = environment.socket_url;
} else {
  var socket_url = 'wss://' + socket_ip + '/esp-ui/distributed/result';
}
let ws;
var Timer_count = 0;
var timer_is_on = 0;
var set_time_out
export interface CustomResponse {
  data: any;
  message: any;
  status: any;
}

@Component({
  selector: 'app-live-queries',
  templateUrl: './live-queries.component.html',
  styleUrls: ['./live-queries.component.css'],
  providers: [NgxSpinnerService]
})
export class LiveQueriesComponent implements AfterViewInit, OnInit,OnDestroy {
  @ViewChild('editor', {static: true}) editor;
  queriesform: FormGroup;

  public taggedList = [];
  public hostedList = [];

  public tag_settings = {};
  public host_settings = {};

  online_nodes: any;
  startedAt: any;
  progress: any = 0;
  countReceived: number = 0;

  loading = false;
  public clicked: boolean = false;
  submitted = false;
  subscription: Subscription;
  dtTrigger: Subject<any> = new Subject();
  table: any;
  systems_with_empty_results=[];
  columns_fetched=false;
  live_queries_table:any;
  liveQuerySchema:any;
  select_tab='false'
  results_status={};
  HostNameWithStatus={};
  searchText:any;
  failed_nodes_percentage: any = 0;
  Failed_nodes_count:number = 0
  expandList:any =[];

  OsNameList = [];
  OsNameListSettings = {};
  OsNamesSelectedItems = [];

  noSchemaData: boolean = false

  searchTerm: any;

  tempheader: any;

  public isRowGrouping: any = 'host_name'

  createKeywordMapper = function (map, defaultToken, ignoreCase,) {
    try{
      var keywords = Object.create(null);
      var $keywordList = null;
      return Object.keys(map).forEach(function (className) {
        var a = map[className];
        ignoreCase && (a = a.toLowerCase());
        for (var list = a.split("|"), i = list.length; i--;) keywords[list[i]] = className;
      }), Object.getPrototypeOf(keywords) && (keywords.__proto__ = null), $keywordList = Object.keys(keywords), map = null, ignoreCase ? function (value) {
        return keywords[value.toLowerCase()] || defaultToken;
      } : function (value) {
        return keywords[value] || defaultToken;
      };
    }
    catch(err){
      console.log(err);
      this.router.navigate(['/live-query']);
    }

  };

  keywordMapper = this.createKeywordMapper({
    "osquerycolumn": all_columns,
    "support.function": builtinFunctions,
    keyword: keywords,
    "constant.language": dataTypes,
    "table": tables,
  }, "identifier", null);
  rules = {
    start: [{
      token: "comment",
      regex: "--.*$"
    }, {
      token: "comment",
      start: "/\\*",
      end: "\\*/"
    }, {
      token: "string",
      regex: '".*?"'
    }, {
      token: "string",
      regex: "'.*?'"
    }, {
      token: "constant.numeric",
      regex: "[+-]?\\d+(?:(?:\\.\\d*)?(?:[eE][+-]?\\d+)?)?\\b"
    }, {
      token: this.keywordMapper,
      regex: "[a-zA-Z_$][a-zA-Z0-9_$]*\\b"
    }, {
      token: "keyword.operator",
      regex: "\\+|\\-|\\/|\\/\\/|%|<@>|@>|<@|&|\\^|~|<|>|<=|=>|==|!=|<>|="
    }, {
      token: "paren.lparen",
      regex: "[\\(]"
    }, {
      token: "paren.rparen",
      regex: "[\\)]"
    }, {
      token: "text",
      regex: "\\s+"
    }]
  };


  constructor(
    private router: Router,
    private fb: FormBuilder,
    private http: HttpClient,
    private commonapi: CommonapiService,
    private _Activatedroute: ActivatedRoute,
    private spinner: NgxSpinnerService,
    private titleService: Title,
    private toastr: ToastrService,
    private columndefs:Datatablecolumndefs,

    private commonvariable: CommonVariableService,
  ) {
    this.queriesform = this.fb.group({
      tags: [],
      hosts: [],
      sql: '',
      OsNames:[]
    });
  }

  initialise_query_editor() {
    this.editor.getEditor().setOptions({
      autoScrollEditorIntoView: true,
      theme: THEME,
      highlightSelectedWord: true,
      enableBasicAutocompletion: true,
      enableLiveAutocompletion: true
    });
    this.editor.getEditor().focus();
    var session = this.editor.getEditor().session;
    var rules = this.rules;
    session.setMode('ace/mode/' + 'text', function () {
        // force recreation of tokenizer
        session.$mode.$highlightRules.addRules(rules);
        session.$mode.$tokenizer = null;
        session.bgTokenizer.setTokenizer(session.$mode.getTokenizer());
        // force re-highlight whole document
        session.bgTokenizer.start(0);
      }
    );

    var staticWordCompleter = {
      getCompletions: function (editor, session, pos, prefix, callback) {
        var all_keywords = tables + "|" + keywords + "|" + all_columns + "|" + dataTypes + "|" + builtinFunctions;
        var all_keywords_list = all_keywords.split("|");
        callback(null, all_keywords_list.map(function (word) {
          var table_array = tables.split("|");
          var meta = '';
          if (keywords.includes(word)) {
            meta = 'keyword';
          } else if (builtinFunctions.includes(word)) {
            meta = 'function';
          } else if (table_array.includes(word)) {
            meta = 'table';
          } else if (all_columns.includes(word)) {
            meta = 'column';
          } else if (dataTypes.includes(word)) {
            meta = 'data_type';
          }
          return {
            caption: word,
            value: word,
            meta: meta
          };
        }));
      }
    }

    langTools.setCompleters([staticWordCompleter]);
    this.editor.completers = [staticWordCompleter];
    this.editor.getEditor().commands.addCommand({
      name: "runQuery",
      bindKey: {
        win: "Ctrl-Enter",
        mac: "Command-Enter"
      },
      exec: function require() {
        $(".query-editor__btn-run").trigger("click");
      }
    })
  }

  ngAfterViewInit() {
    this.dtTrigger.next();
    this.initialise_query_editor();
  }

  ngOnInit() {
    $.fn.dataTable.ext.errMode = 'none';
    this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Live query");

    this._Activatedroute.paramMap.subscribe(params => {
      let live_queryid = params.get('id');
      if (live_queryid !== null) {
        this.commonapi.get_Query_data(live_queryid).subscribe((res: CustomResponse) => {
          this.editor.value = res.data.sql;
        });
      }
    });
    this.OsNameListSettings = {
      singleSelection: false,
      text: "Select by Operating System",
      selectAllText: 'Select All OS Names',
      unSelectAllText: 'Unselect All',
      badgeShowLimit: 1,
      enableSearchFilter: true,
      classes: "Operating_system-class",
      searchPlaceholderText: "Search OS Name here.."
    };

    this.commonapi.Hosts_data().subscribe((res: CustomResponse) => {
      var ListOfOs=[]
      for (const i in res.data.results) {
        if(res.data.results[i].state == 0)
        {
          this.hostedList.push({id: res.data.results[i].id, host_identifier: res.data.results[i].host_identifier, itemName: res.data.results[i].display_name, osName:res.data.results[i].os_info['name']});
          ListOfOs.push(res.data.results[i]['os_info'].name)
        }
      }
      ListOfOs=ListOfOs.filter((value,index)=>ListOfOs.indexOf(value)===index)
      for(const i in ListOfOs){
        this.OsNameList.push({id:i, itemName:ListOfOs[i]});
      }

      this.host_settings = {
        singleSelection: false,
        text: "Select by Hosts",
        selectAllText: 'Select All Hosts',
        unSelectAllText: 'Unselect All Hosts',
        badgeShowLimit: 1,
        enableSearchFilter: true,
        classes: "tag-class",
        searchBy:["itemName"],
        searchPlaceholderText: "Search host here.."
      };
    });
    this.commonapi.Tags_data().subscribe((res: CustomResponse) => {
      for (const i in res.data.results) {
        this.taggedList.push({id: i, itemName: res.data.results[i].value});
      }
      this.tag_settings = {
        singleSelection: false,
        text: "Select by Tags",
        selectAllText: 'Select All Tags',
        unSelectAllText: 'Unselect All Tags',
        badgeShowLimit: 1,
        enableSearchFilter: true,
        classes: "tag-class",
        searchPlaceholderText: "Search tag here.."
      };

    });
    this.LiveQueryTableSchema();

  }

  LiveQueryTableSchema(){
           this.commonapi.live_Queries_tables_schema().subscribe((res: CustomResponse) => {
             var _arraytable = [];
             var _arraycolumn = []
             this.live_queries_table = res.data;
             this.liveQuerySchema = res.data;
             $('.table_loader').hide();
             this.search_tables();
             this.live_queries_table.forEach(function (table) {
                 _arraytable.push(table.name);
                 _arraycolumn.push(Object.keys(table.schema));
             });
             var _tablestring = _arraytable.toString();
             var _columnstring = _arraycolumn.toString();
             var _newchar = '|'
             var _livequerytabledata = _tablestring.split(',').join(_newchar);
             var _livequerycolumndata = _columnstring.split(',').join(_newchar);
             localStorage.setItem("Livequerytable", _livequerytabledata);
             localStorage.setItem("Livequerycolumn", _livequerycolumndata);
           })
  }

  get f() {
    return this.queriesform.controls;
  }


  onItemSelect(item: any) {
  }

  OnItemDeSelect(item: any) {

  }

  onSelectAll(items: any) {
  }

  onDeSelectAll_hosts(items: any) {
    this.queriesform.controls['hosts'].reset()
  }
  onDeSelectAll_tags(items: any) {
    this.queriesform.controls['tags'].reset()
  }
 OnDeSelectAllOsNames(items: any) {
    this.OsNamesSelectedItems=[]
  }

  public onSubmit() {
    this.select_tab='false'
    this.failed_nodes_percentage=0
    Timer_count=0
    this.searchText = undefined;
    this.systems_with_empty_results=[];
    this.columns_fetched=false;
    if (ws != undefined) {
      ws.close();
    }
    this.countReceived = 0;
    this.startedAt=new Date().getTime();
    this.progress = 0;
    this.submitted = true;
    $("#results").empty();
    this.table = undefined;


    if (this.queriesform.invalid) {
      return;
    }


    var sql = this.editor._text;
    let tags = this.f.tags.value;
    let hosts = this.f.hosts.value;

    var selected_tag = '';
    for (const i in tags) {
      selected_tag = selected_tag + ',' + tags[i].itemName;
    }
    var selected_hosts = '';
    for (const i in hosts) {
      selected_hosts = selected_hosts + ',' + hosts[i].host_identifier;
    }
    var SelectedOSNames=[];
    for (const i in this.OsNamesSelectedItems) {
      SelectedOSNames.push(this.OsNamesSelectedItems[i]['itemName']);
    }
    let queryObj = {
      "tags": selected_tag,
      "query": sql,
      "nodes": selected_hosts,
      "os_name":SelectedOSNames
    }
    if (sql !== '') {
      if (selected_tag !== '' || selected_hosts !== '' || SelectedOSNames.length!=0) {
        this.clicked = true;
        setTimeout(() => {
          this.clicked = false;
        }, 5000);

        this.commonapi.Queries_add_api(queryObj).subscribe((res: CustomResponse) => {
          var data = res;
          this.HostNameWithStatus={}
          if(data.status == 'success'){
            for(const i in data.data.online_nodes_details){
              this.HostNameWithStatus[data.data.online_nodes_details[i].node_id]={"hostname":data.data.online_nodes_details[i].hostname,"status":"Pending"}
            }
            currentQueryID = data.data.query_id;
          }else{
            this.clicked = false;
            swal({
              icon: 'warning',
              title: data.status,
              text: data.message,
            });
          }

          this.online_nodes = data.data.onlineNodes;
          this.connect(data.data.query_id);
          window.addEventListener('offline', () =>   this.toastr.error('Network disconnected!.\n You may  not receive any pending results. Try sending the query again\ once connected'));

        });

      } else {
        swal({
          icon: 'warning',
          text: 'Please Select Hosts/Tags/Operating System',
        });
      }
    } else {
      swal({
        icon: 'warning',
        text: 'Query is Required',
      });

    }
    this.loading = false;
    if (this.subscription) {
      this.subscription.unsubscribe();
    }

  }

  connect(queryId) {
    var timeNow = new Date().getTime();
    var timeElapsed = (timeNow - this.startedAt)/60000;
    if(queryId==currentQueryID && this.online_nodes!=this.countReceived && timeElapsed<10){
      // Should connect only if listening to the current triggered query and only if results are not received for all the nodes and only if time elapsed is not greater than 10 min
      console.log("Connecting to websocket...");
      ws = new WebSocket(socket_url);
      console.log(queryId);
      this.select_tab='true'
      function timedCount() {
        Timer_count = Timer_count + 1;
        set_time_out = setTimeout(timedCount, 1000);
        if(Timer_count==120 && that.progress!=100){
          Swal.fire({title:"Please wait.Executing..."})
        }
        if(Timer_count==300 && that.progress!=100){
          Swal.fire({title:"Taking longer time than expected.Please try again"})
          that.failed_nodes_percentage=(100-that.progress).toFixed(2)
          that.Failed_nodes_count=that.online_nodes-that.countReceived
          clearTimeout(set_time_out)
          timer_is_on=0
        }
      }
      ws.onopen = function () {
        ws.send(queryId);
      };
      var that = this;
      ws.onmessage = function (e) {
        try {
          var data = e.data;
            if (data instanceof Blob) {
              if (!timer_is_on) {
                timer_is_on = 1;
                timedCount();
              }else{
                Timer_count=0
              }
              var reader = new FileReader();
              reader.addEventListener('loadend', (event: Event) => {
                const text = reader.result as string;
                var txtResult;
                if (typeof text === 'object'){
                    txtResult = text // dont parse if its object
                }
                else if (typeof text === 'string'){
                    txtResult = JSON.parse(text); // parse if its string
                }

                  var response_data = txtResult;
                  $('.Live_queries_results_loader').hide();

                  if(currentQueryID==response_data.query_id){
                  if(that.HostNameWithStatus[response_data.node.id].status=="Success" || that.HostNameWithStatus[response_data.node.id].status=="Failure"){
                    console.log("Got results again for node with id " + that.HostNameWithStatus[response_data.node.id]);
                  }else{
                    if(that.HostNameWithStatus.hasOwnProperty(response_data.node.id)){
                      if(response_data.status==0){
                        that.HostNameWithStatus[response_data.node.id].status="Success";
                      }else{
                        that.HostNameWithStatus[response_data.node.id].status="Failure";
                      }
                    }
                    /* Start - adding hostname into json */
                    var data = response_data.data;
                    for (const i in data) {
                      data[i]['host_name'] = response_data.node.name;
                    }
                    /* End - adding hostname into json */
                    that.populateTable(data,response_data.node.name,response_data.node.id);
                  }
                }


              });
              reader.readAsText(data);
            }
        } catch (err) {
            console.log(err);
        }
      };

      ws.onclose = function (e) {
          console.log('Socket has been closed.', e.reason);
          setTimeout(function () {
            that.connect(queryId);
          }, 2000);
      };

      ws.onerror = function (err) {
        console.error('Socket encountered error: ', err, 'Closing socket');
        ws.close();
      };
    }
}


  populateTable(res_data, node_name, nodeID) {

    this.loading = false;
    this.countReceived = this.countReceived + 1;
    if(this.online_nodes==this.countReceived){
      ws.close(); /* closing socket as received results of all nodes */
    }
    this.progress = ((100 * this.countReceived) / this.online_nodes).toFixed(2);
    if(this.failed_nodes_percentage!=0){
      this.failed_nodes_percentage=(100-this.progress).toFixed(2)
      this.Failed_nodes_count=this.online_nodes-this.countReceived
    }
    var nodeTitle = $('<h5/>');

    nodeTitle.css("margin-top", "10px");
    if (res_data.length == 0) {
      // adding/creating table with empty data
      if(this.HostNameWithStatus[nodeID].status=="Failure"){
        this.systems_with_empty_results.push({"host_name": node_name+" - Failure"});
        res_data=[{"host_name": node_name+" - Failure"}];
      }else{
        this.isRowGrouping = 'false'
        this.systems_with_empty_results.push({"host_name": node_name+" - No Data"});
        res_data=[{"host_name": node_name+" - No Data"}];
      }
      if (this.table != undefined) {
        this.add_to_existing_table(res_data);
      } else {
        this.draw_new_table(res_data);
      }
    } else {
      this.isRowGrouping = 'host_name'
      // recreating table with new columns
      if (!this.columns_fetched) {
        this.columns_fetched = true;
        this.table = undefined;

        $("#results").empty();
        this.draw_new_table(res_data);

        for (let empty_system_data in this.systems_with_empty_results) {
          this.add_to_existing_table([this.systems_with_empty_results[empty_system_data]]);
        }
      } else {
        this.add_to_existing_table(res_data);
      }
    }
  }

  draw_new_table(res_data) {
    console.log('drawing')
    var keys = Object.keys(res_data[0]);
    keys.unshift(keys.pop())

    var columns = [];


    var _result = this.columndefs.columnDefs(keys);
    var column_defs = _result.column_defs;
    columns = _result.column;

    var newTable = $("<table></table>")
      .attr("id", "live_query_table")
      .attr("style", "margin-left:auto;width:100%;overflow-x: scroll")
      .attr("width", "100%;")
      .attr("font-weight", "normal")
      .addClass("table table-striped- table-hover table-checkable display dt-body-left list_table lq-custom-pagination table-controls");


    // });
    $('#results').append(newTable);
    var currentDate = new Date();
    var data_row = res_data;
    let table = newTable.DataTable({
      "searching": true,
      "orderCellsTop": true,
      "aoColumns": columns,
      "scrollX": false,
      "lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
      "bScrollCollapse": true,
      "sPaginationType": "full_numbers",
      "lengthChange": false,
      "bJQueryUI": true,
      "dom": "Blfrt<'row table-controls'<'col-sm-6 table-controls-li'i><'col-sm-6'p>>",
      // "sDom": 'r<"H"lf><"datatable-scroll"t><"F"ip>',
      "language": {
        "search": "Search: ",
        "info" : "Showing _START_ to _END_ of <b>_TOTAL_</b> entries"
      },
      "rowGroup": {
        dataSrc: this.isRowGrouping
      },
      "initComplete": function (settings, json) {
          $("#live_query_table").wrap("<div style='overflow:auto; width:100%;position:relative;max-height:70vh;margin-top:10px'></div>");
          $('.list_table thead tr').clone(true).addClass('filter-row').appendTo('.list_table thead');
          $("#live_query_table thead tr.filter-row th").each(function() {
            $(this).replaceWith('<td>' + $(this).text() + '</td>');
            $(this).wrapInner('<div />').find('div').unwrap().wrap('<td/>');
          });
          $('#live_query_table_filter').hide()
       },
      "buttons": [
        {
          extend: 'excelHtml5',
          title: 'live_query_results_' + currentDate.getFullYear() + '-' + (currentDate.getMonth() + 1) + '-' + currentDate.getDate()
        },
        {
          extend: 'csvHtml5',
          title: 'live_query_results_' + currentDate.getFullYear() + '-' + (currentDate.getMonth() + 1) + '-' + currentDate.getDate()
        }
      ],
      "columnDefs":column_defs,
      "drawCallback": function (settings, start, end, max, total, pre) {
        var records_display = this.fnSettings().fnRecordsDisplay();
        if (records_display == 0) {
          $(".dataTables_scrollHeadInner").addClass("dataTables_Headerscrollx");
          $('#undefined_table tbody').addClass('no_records');
        } else {
          $('#undefined_table tbody').removeClass('no_records');
          $(".dataTables_scrollHeadInner").removeClass("dataTables_Headerscrollx");
        }
      },
      rowCallback: function (row, data, index) {
        $('td', row).css('background-color', 'white');
        $('td', row).css('font-size', '13px');
      }
    });
    this.table=table;
    /* adding column search Start */

    $('.list_table thead tr:eq(1) td').each(function (i) {
      var title = $(this).text();
      $(this).html('<input type="text" placeholder="Search ' + title + '" />');

      $('input', this).on('keyup change', function () {
        if (table.column(i).search() !== this.value) {
          table
            .column(i)
            .search(this.value)
            .draw();
        }

      });
    });
    /* adding column search End */

    /* Adding new row in datatable Start*/
    newTable.dataTable().fnAddData(data_row);
    /* Adding new row in datatable End*/

    /* Adjusting header in datatable Start*/
    $('#container').css('display', 'block');
    table.columns.adjust().draw();
    $('.list_table thead tr th').each(function (i) {
          $(this).removeClass('sorting_asc');
    });
    /* Adjusting header in datatable End*/
  }

  changetab(){
    if(this.table != undefined){
      setTimeout(()=>{
          this.table.columns.adjust().draw(true);
       },50);
    }
  }
  tableSearch(){
    this.searchTerm = (<HTMLInputElement>document.getElementById('customsearch')).value
    var oTable = $('#live_query_table').DataTable()
    oTable.search(this.searchTerm).draw()
    if(oTable.page.info().recordsDisplay == 0){
      this.tempheader = $('.filter-row').html()
      $('.filter-row').html('<td colspan=' +oTable.columns().nodes().length + '>No Matching Records Found</td>')
    }
    else if(oTable.page.info().recordsDisplay > 0){
      $('.filter-row').html(this.tempheader)
    }
  }

  add_to_existing_table(res_data) {
    $('#live_query_table').DataTable().rows.add(res_data).draw(false);
  }
  search_tables(){
    var that = this;
    var searchTerm, panelContainerId;
    var allHidden;
    // Create a new contains that is case insensitive
    $.expr[':'].containsCaseInsensitive = function (n, i, m) {
      return jQuery(n).text().toUpperCase().indexOf(m[3].toUpperCase()) >= 0;
    };

    $('#accordion_search_bar').on('change keyup paste click', function () {
      if(that.expandList.length != 0){
        that.collapseOpenTable(that.expandList);
      }
      searchTerm = $(this).val();
      $('.panel > .card-header').each(function () {
        panelContainerId = '#' + $(this).attr('id');
        $(panelContainerId + ':not(:containsCaseInsensitive(' + searchTerm + '))').hide();
        $(panelContainerId + ':containsCaseInsensitive(' + searchTerm + ')').show();
      });
      if($('.panel > .card-header').children(':visible').length == 0) {
        // action when all are hidden
        allHidden = true
        that.noSchemaData = true
     }
     else{
        allHidden = false
        that.noSchemaData = false
     }
    });
  }
  expand(indexId){
    var filterData = this.expandList.find(x=>x == indexId);
    if(typeof filterData == 'undefined'){
      this.expandList.push(indexId);
    }
    else{
      this.expandList = this.expandList.filter(x=>x !== indexId);
    }
  }
  collapseOpenTable(list){
    list.forEach(function (expandId) {
      var div = document.getElementById(expandId);
      if(div != null){
        div.classList.remove("show");
      }
     });
     this.expandList = [];

  }
  changePlatform(platForm){
    var tempList = [];
    this.live_queries_table = this. liveQuerySchema;
    if(platForm != 'All'){
      this.live_queries_table.forEach(function (res) {
           var filterData = res.platform.find(x=>x == platForm);
           if(typeof filterData != 'undefined'){
             tempList.push(res);
           }
       });
       this.live_queries_table = tempList;
    }
  }
  ngOnDestroy() {
    Swal.close();
    let bodyTemplast = document.getElementsByTagName("BODY")[0];
    bodyTemplast.classList.remove("kt-aside--minimize");
    bodyTemplast.classList.remove("kt-aside--minimize-hover");
    clearTimeout(set_time_out)
  }
}
