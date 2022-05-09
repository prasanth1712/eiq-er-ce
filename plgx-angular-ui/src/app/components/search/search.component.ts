import { AfterViewInit,Component, OnInit,ViewChild  } from '@angular/core';
import { QueryBuilderConfig, QueryBuilderComponent, QueryBuilderClassNames } from 'angular2-query-builder';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { DataTableDirective } from 'angular-datatables';
import { Subject } from 'rxjs';
import {NgDatepickerModule, DatepickerOptions} from 'ng2-datepicker';
import {NgModule} from '@angular/core';
import Swal from 'sweetalert2';
import {NgbDateStruct,NgbDate, NgbCalendar} from '@ng-bootstrap/ng-bootstrap';
declare function populateNodeData(any): any;
declare var $: any;
var PaginationIndex
var TempIndex
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
@NgModule({
  imports: [
    NgDatepickerModule
  ],

})
export class SearchComponent implements AfterViewInit,OnInit {
  @ViewChild(DataTableDirective, {static: false})
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
    inputControl: 'form-control',
    inputControlSize: 'q-control-size'
  };

  public OperatorMap = {
      string: ['equal','contains']
  };

  config: QueryBuilderConfig = {
    fields: {
      empty: {name: 'Nothing Selected', type:'none'},
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
  this.loading = true;
  var ruleQueryValue = this.query.rules.find(x=>typeof x.value == 'undefined');
  if(this.query.rules.length==0 || typeof ruleQueryValue != 'undefined' || this.selectedDate['date'] == null){
    this.loading = false;
    Swal.fire({
      icon: "warning",
      text: "Please provide valid input",
    })
  }else{
    this.PreviousDataIds={}
    NextDataId=0
    this.search_data["conditions"]=this.query;
    this.Rerender_datatable()
    $("#table_noresults").hide()
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
      "language": {
        "search": "Search: ",
        "paginate": {
          "first":'first',
          "last":'last',
          "previous": '<i class="fas fa-angle-double-left"></i> Previous',
          "next": 'Next <i class="fas fa-angle-double-right"></i>',
        },
      },
      ajax: (dataTablesParameters: any,callback) => {
        var selectedDate = this.selectedDate['date'];
        var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
        var body = dataTablesParameters;
        body['limit']=body['length'];
        if((this.query.rules).length==0){
          return
        }
        PaginationIndex=body['start']
        if(PaginationIndex>TempIndex)   //checking next page index
        {
          body['start']=NextDataId
        }
        else if (PaginationIndex<TempIndex)  //checking Previous page index
        {
          body['start']=this.PreviousDataIds[PaginationIndex]
        }
        TempIndex=PaginationIndex;
       body["conditions"]=this.search_data['conditions']
       body["date"]= date;
       body["duration"]=this.selectedDate['duration'];
        this.http.post<DataTablesResponse>(environment.api_url + "/activity/search", body, {
          headers: {
            'Content-Type': 'application/json',
            'x-access-token': localStorage.getItem('token')
          }
        }).subscribe(res => {
          this.loading = false
          if(res['status']=='success'){
            this.search_data_output=res.data['results']
            if(res.data['count'] > 0 && res.data['results'] != undefined)
            {
              this.PreviousDataIds[PaginationIndex]=(this.search_data_output[0].id)+1
              NextDataId=(this.search_data_output[this.search_data_output.length - 1]).id
              $('.table_data').show();
              $('.dataTables_paginate').show();
              $('.dataTables_info').show();
              $('.dataTables_filter').show()
              $("#table_noresults").hide()
            }
            else{
              $('.dataTables_paginate').hide();
              $('.dataTables_info').hide();
              $('.table_data').show();
              $("#table_noresults").show()

            }
            callback({
              recordsTotal: res.data['count'],
              recordsFiltered: res.data['count'],
              data: []
            });
          }if(res['status']=='failure'){
            $("#table_noresults").hide()
            $('.table_data').hide();
            Swal.fire({
              icon: "warning",
              text: "Please check the missing Condition",
              //text: res['message'],
            })
          }
        });
      },
      ordering: false,
      columns: [{data: 'hostname'}]
    };
    $(document).on( 'click', '.paginate_button', function (e) {
      if(!(e.currentTarget.className).includes('disabled')){
          $('.paginate_button.next').addClass('disabled');
          $('.paginate_button.previous').addClass('disabled');
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
      this.Rerender_datatable()
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
    // this.datepicker_date['duration']=duration_period;
    this.selectedDate['duration']=duration_period;
    this.Rerender_datatable()
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
