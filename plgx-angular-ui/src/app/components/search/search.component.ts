import { AfterViewInit,Component, OnInit,ViewChild  } from '@angular/core';
import { QueryBuilderConfig, QueryBuilderComponent, QueryBuilderClassNames } from 'angular2-query-builder';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { DataTableDirective } from 'angular-datatables';
import { Subject } from 'rxjs';
import { DatepickerOptions} from 'ng2-datepicker';
import {NgModule} from '@angular/core';
import Swal from 'sweetalert2';
import {NgbDateStruct,NgbDate, NgbCalendar} from '@ng-bootstrap/ng-bootstrap';
declare function populateNodeData(any): any;
declare var $: any;
var PaginationIndex
var TempIndex
var PaginationLength
var TempLength = PaginationLength = 10;
var NextDataId
class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}
import 'datatables.net';



@Component({
  selector: 'app-search',
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css'],

})

export class SearchComponent implements AfterViewInit,OnInit {
  @ViewChild(DataTableDirective)
  dtElement: DataTableDirective;
  dtTrigger: Subject<any> = new Subject();
  dtOptions: DataTables.Settings = {};
  loading = false;
  datepicker_date = {};
  public search_data:any={};
  search_data_output:any;
  myjson: any = JSON;
  selectedDate = {};
  maxDate:any;
  PreviousDataIds={}
  isSubmitted: boolean = false;
  constructor(
    private http: HttpClient,
    private calendar: NgbCalendar,
  ) { var today = new Date(); this.maxDate = { year:today.getFullYear(),month: today.getMonth()+1, day: today.getDate()+1} }

  public bootstrapClassNames: QueryBuilderClassNames = {
    arrowIconButton: 'q-arrow-icon-button',
    arrowIcon: 'q-icon q-arrow-icon',
    removeIcon: 'fa fa-times',
    addIcon: 'fa fa-plus',
    button: 'btn btn-sm btn-outline-success',
    buttonGroup: 'btn-group pull-right group-actions',
    removeButton: 'btn btn-sm btn-outline-danger',
    switchGroup: 'q-switch-group',
    switchLabel: 'q-switch-label',
    switchRadio: 'q-switch-radio',
    rightAlign: 'q-right-align',
    transition: 'q-transition',
    collapsed: 'q-collapsed',
    treeContainer: 'q-tree-container',
    tree: 'q-tree',
    row: 'q-row',
    connector: 'q-connector',
    rule: 'q-rule',
    ruleSet: 'q-ruleset',
    invalidRuleSet: 'q-invalid-ruleset',
    emptyWarning: 'q-empty-warning',
    fieldControl: 'form-control',
    fieldControlSize: 'q-control-size',
    entityControl: 'form-control',
    entityControlSize: 'q-control-size',
    operatorControl: 'form-control',
    operatorControlSize: 'q-control-size',
    inputControl: 'form-control query-input',
    inputControlSize: 'q-control-size'
  };

  public OperatorMap = {
      string: ['equal','contains']
  };

  config: QueryBuilderConfig = {
    fields: {
      empty: {name: 'Nothing Selected', type:'string'},
      md5: {
        name: 'md5',
        type: 'string',
      },
      domain_name: {
        name: 'domain_name',
        type: 'string',
      },
      sha256: {
        name: 'sha256',
        type: 'string',
      },
      ja3_md5: {
        name: 'ja3_md5',
        type: 'string',
      },
      process_guid: {
        name: 'process_guid',
        type: 'string',
      },
      parent_process_guid: {
        name: 'parent_process_guid',
        type: 'string',
      },
      target_path: {
        name: 'target_path',
        type: 'string',
      },
      target_name: {
        name: 'target_name',
        type: 'string',
      },
      process_name: {
        name: 'process_name',
        type: 'string',
      },
      remote_address: {
        name: 'remote_address',
        type: 'string',
      }

    }
  }

  query = {
    condition: 'AND',
    rules: []
  };
  allowRuleset = true;
  allowCollapse = false;


search(){

  this.isSubmitted = true;
  //Checking all input fields available
  let inputfields = document.getElementsByClassName("query-input");
  let isAnyInputEmpty: boolean = false
  for(var i = 0; i<inputfields.length; i++){
    if((inputfields[i] as HTMLInputElement).value == '' || (inputfields[i] as HTMLInputElement).value.replace(/\s/g, '').length == 0){
      isAnyInputEmpty = true
    }
  }

  const tempDateSelected = new Date(this.selectedDate['date'].year, this.selectedDate['date'].month, this.selectedDate['date'].day);
  const tempDateMax = new Date(this.maxDate.year, this.maxDate.month, this.maxDate.day);
  this.loading = true;

  if(isAnyInputEmpty || inputfields.length == 0){
    this.isSubmitted = false
    this.loading = false;
    Swal.fire({
      icon: "warning",
      text: "Please provide valid input",
    })
  }else if(tempDateSelected > tempDateMax ||  tempDateSelected.toDateString() == 'Invalid Date' || this.selectedDate['date'] == null) {
    this.isSubmitted = false
    this.loading = false;
    Swal.fire({
      icon: "warning",
      text: "Please provide correct date input",
    })
  }else{
    this.PreviousDataIds={}
    NextDataId=0
    this.search_data["conditions"]=this.query;
    this.Rerender_datatable()
    $('.table_data').hide();
  }
}

  ngOnInit() {
    $('.table_data').hide();
    this.getDate()
  }

  ngAfterViewInit(): void {
    this.dtTrigger.next();
  }
  ngOnDestroy(): void {
    this.dtTrigger.unsubscribe();
  }

  get_dtOptions( ){
    this.dtOptions = {
      pagingType: 'simple',
      pageLength: 10,
      serverSide: true,
      processing: true,
      searching: false,
      dom: "<'row'<'col-sm-12'f>>" +
      "<'row table-scroll-hidden table-scroll-hidden-hunt'<'col-sm-12 mt-18 table-scroll full-height'tr>>" +
      "<'row table-controls custom-pagination-margin custom-pagination-margin-hunt'<'col-sm-6 d-flex align-items-center table-controls-li pl-0'li><'col-sm-6 pr-0 paginate_button-processing'p>>",
      "initComplete": function (settings, json) {
        $("#search_table").wrap("<div style='overflow:auto; width:100%;position:relative;'></div>");
       },
      "language": {
        "search": "Search: ",
        "lengthMenu": "<ng-container class=custom-pagination-length>Results per page: _MENU_</ng-container>",
        "info" : "Showing _START_ to _END_ of <b>_TOTAL_</b> entries",
      },
      ajax: (dataTablesParameters: any,callback) => {
        var selectedDate = this.selectedDate['date'];
        var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
        if(date == 'undefined-undefined-undefined'){
          Swal.fire({
            icon: "warning",
            text: "Please provide correct date input",
          })
          $('#DataTables_Table_0_processing').hide();
          return;
        }
        var body = dataTablesParameters;
        body['limit']=body['length'];
        if((this.query.rules).length==0){
          return
        }
        PaginationIndex = body['start']
        PaginationLength = body['length']
        
        if(PaginationLength != TempLength){ //If pagination length is changed
          dataTablesParameters.start = 0
          body['start'] = 0
          var table = $("#search_table").DataTable();
          table.page(0)
          PaginationIndex = 0
        }
        else if(PaginationIndex>TempIndex)   //checking next page index
        {
          body['start']=NextDataId
        }
        else if (PaginationIndex<TempIndex)  //checking Previous page index
        {
          body['start']=this.PreviousDataIds[PaginationIndex]
        }
        
        TempIndex = PaginationIndex;
        TempLength = PaginationLength;
       body["conditions"]=this.search_data['conditions']
       body["date"]= date;
       body["duration"]=this.selectedDate['duration'];
        let timeoutdone: boolean = false;
        setTimeout(function () {
          timeoutdone = true
        }, environment.nginx_timeout? environment.nginx_timeout: 120000)
        this.http.post<DataTablesResponse>(environment.api_url + "/activity/search", body, {
          headers: {
            'Content-Type': 'application/json',
            'x-access-token': localStorage.getItem('token')
          }
        }).subscribe(
          res => {
          this.isSubmitted = false;
          this.loading = false
          if (res['status'] == 'success') {
            this.search_data_output = res.data['results']
            if (res.data['count'] > 0 && res.data['results'] != undefined) {
              this.PreviousDataIds[PaginationIndex] = (this.search_data_output[0].id) + 1
              NextDataId = (this.search_data_output[this.search_data_output.length - 1]).id
              $('.table_data').show();
              $('.dataTables_paginate').show();
              $('.dataTables_info').show();
              $('.dataTables_filter').show()
            }
            else {
              $('.dataTables_paginate').hide();
              $('.dataTables_info').hide();
              $('.table_data').show();

            }
            callback({
              recordsTotal: res.data['count'],
              recordsFiltered: res.data['count'],
              data: []
            });
          } if (res['status'] == 'failure') {
            $('.table_data').hide();
            Swal.fire({
              icon: "warning",
              text: "Please check the missing Condition",
              //text: res['message'],
            })
          }
        },err =>{
          if (timeoutdone && (err.status == 502 || err.status == 504)) {
            this.loading = false
            $('.table_data').hide();
            Swal.fire({
              icon: 'error',
              text: 'Request timed out because server is busy. Please try again later.'
            })
          }
          else{
            Swal.fire({
              icon: 'error',
              text: err.statusText
            })
          }
        });
      },
      ordering: false,
      columns: [{data: 'hostname'}]
    };
    $(document).on( 'click', '.paginate_button', function (e) {
      if(!(e.currentTarget.className).includes('disabled')){
          $('.paginate_button-processing .paginate_button.next').addClass('disabled');
          $('.paginate_button-processing .paginate_button.previous').addClass('disabled');
      }})
  }
  getDate() {
    var today = new Date();
    var date = today.getFullYear() + '-' + (today.getMonth() + 1) + '-' + today.getDate();
    // this.datepicker_date['date']=date;
    // this.datepicker_date['duration']=3;
    // this.getconverted_date()
    this.selectedDate['date'] = this.calendar.getToday();
    this.selectedDate['duration']=3;
    this.get_dtOptions()

}
getconverted_date() {
    var date =  this.datepicker_date['date'];
    if(date instanceof Date){
      date=this.convertDate(date);
      this.datepicker_date['date']=date
    }
  }
  myHandler(){
    // this.getconverted_date()
    if(this.selectedDate['date'] != null){
      if(this.isSubmitted)
      {
        this.Rerender_datatable()
      }
    }else{
      Swal.fire({
        icon: "warning",
        text: "Please provide valid input",
      })
    }

  }
  convertDate(date) {
    var  mnth = ("0" + (date.getMonth() + 1)).slice(-2),
      day = ("0" + date.getDate()).slice(-2);
    return [date.getFullYear(), mnth, day].join("-");
  }
  get_duration(duration_period){
    this.selectedDate['duration']=duration_period;
  }
  Rerender_datatable(){
    this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
      // Destroy the table first
      dtInstance.destroy();
      // Call the dtTrigger to rerender again
      this.dtTrigger.next();
    });
  }
  action(event): void {
    event.stopPropagation();
  }
}
