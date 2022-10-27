import { AfterViewInit,Component, OnInit,ViewChild } from '@angular/core';
import { FormControl, FormGroup, FormBuilder, Validators, FormArray } from '@angular/forms';
import { Location } from '@angular/common';
import { DataTableDirective } from 'angular-datatables';
import { Subject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { HttpClient } from '@angular/common/http';
import { Subscription } from 'rxjs';
import {DatepickerOptions} from 'ng2-datepicker';
import {NgModule} from '@angular/core';
import Swal from 'sweetalert2';
import { ToastrService } from 'ngx-toastr';
import {NgbDateStruct,NgbDate, NgbCalendar,NgbInputDatepickerConfig} from '@ng-bootstrap/ng-bootstrap';
var PaginationIndex
var TempIndex
var PaginationLength
var TempLength = PaginationLength = 10
var NextDataId
var SelectedNodeID = undefined
class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}
@Component({
  selector: 'app-hunt',
  templateUrl: './hunt.component.html',
  styleUrls: ['./hunt.component.css']
})

export class HuntComponent implements AfterViewInit,OnInit {
  @ViewChild(DataTableDirective)
  dtElement: DataTableDirective;
  dtTrigger: Subject<any> = new Subject();
  dtOptions: DataTables.Settings = {};
  md5form: FormGroup;
  loading = false;
  submitted = false;
  indicatorFile:File;
  indicatorFileSizeError: boolean= false;
  maxFileSize: any = 2000000;
  dropdownPacknameList = [];
  selectedPacknameItems = [];
  dropdownPacknameSettings = {};
  huntObj = {};
  searchDataOutput:any
  search_data_output:any
  myjson: any = JSON;
  datepickerDate = {};
  selectedDate = {};
  PreviousDataIds={}
  maxDate:any={};
  constructor(
    private fb: FormBuilder,
    private _location: Location,
    private http: HttpClient,
    private calendar: NgbCalendar,
    private config: NgbInputDatepickerConfig,
    private toastr: ToastrService,
  ) { }

  ngOnInit() {
    this.dropdownPacknameList = [
      {"id":"md5","itemName":"MD5"},
      {"id":"sha256","itemName":"SHA256"},
      {"id":"domain_name","itemName":"Domain Name"},
      {"id":"ja3_md5","itemName":"Certificates"},
    ];
    this.dropdownPacknameSettings = {
      singleSelection: true,
      text:"Select Hunt Type",
      unSelectAllText:'UnSelect All',
      enableSearchFilter:true,
      lazyLoading: false,
      classes: "angular-multiselect-class",
      searchPlaceholderText: "Search Hunt Type here..",
      enableCheckAll: false,
      searchBy: ["itemName"],
    };

    this.md5form= this.fb.group({
      indicatorFile: ['',Validators.required],
      huntType:['',Validators.required]
    });

    $('.table_data').hide();
    this.getDate()
    if((typeof environment.file_max_size == 'number') && environment.file_max_size> 0 && environment.file_max_size< 1073741824){
      this.maxFileSize = environment.file_max_size
    }

  }
  get f() { return this.md5form.controls; }


  uploadFile(event){
    if (event.target.files.length > 0) {
      if(event.target.files[0].size > this.maxFileSize){
        Swal.fire({
          icon: 'warning',
          text: 'Max file size is ' + (this.maxFileSize / 1048576).toFixed(2) + 'MB'
          })
          this.indicatorFileSizeError = true
          this.indicatorFile =undefined;
          (document.getElementById('indicator_file') as HTMLInputElement).value = '';
          this.md5form.get('indicatorFile').reset();
      }
      else{
        this.indicatorFile = event.target.files;
        this.indicatorFileSizeError = false
      }
    }
    else{
      this.indicatorFile =undefined
      this.indicatorFileSizeError = true
    }

  }
onSubmit(){
  this.submitted = true;
  $('.table_data').hide();
  var isvaliddate = this.isDateValid();
  if(!isvaliddate){
    this.dateIncorrectErrorMsg();
    return;
  }
  if (this.md5form.invalid) {
      return;
  }
  this.PreviousDataIds={}
  NextDataId=0
  PaginationIndex = undefined
  TempIndex = undefined
  this.loading = true;
  this.RerenderDatatable()
  $("#table_noresults").hide()
  $('.table_data').show();
}

goBack(){
  this._location.back();
}
onItemSelect(item:any){
  console.log(this.selectedPacknameItems);
}
OnItemDeSelect(item:any){
  console.log(this.selectedPacknameItems);
}
onSelectAll(items: any){
  console.log(items);
}
onDeSelectAll(items: any){
  this.md5form.controls['huntType'].reset()
}
getHuntList( ){
  this.dtOptions = {
    pagingType: 'simple',
    pageLength: 10,
    serverSide: true,
    processing: true,
    searching: false,
    "language": {
      "search": "Search: ",
      "info" : "Showing _START_ to _END_ of <b>_TOTAL_</b> entries",
      "lengthMenu": "<ng-container class=custom-pagination-length>Results per page: _MENU_</ng-container>",
    },
    dom: "<'row'<'col-sm-12'f>>" +
    "<'row table-scroll-hidden table-scroll-hidden-hunt'<'col-sm-12 mt-18 table-scroll full-height'tr>>" +
    "<'row table-controls custom-pagination-margin custom-pagination-margin-hunt'<'col-sm-6 d-flex align-items-center table-controls-li pl-0'li><'col-sm-6 pr-0 paginate_button-processing'p>>",
    "initComplete": function (settings, json) {
      if(!($('#hunt-wrapper').length)){
        $("#hunt_table").wrap("<div id='hunt-wrapper' style='overflow:auto; width:100%;position:relative;'></div>");
      }
     },
    ajax: (dataTablesParameters: any,callback) => {
      var body = dataTablesParameters;
            var uploadData = new FormData();
            PaginationIndex = body['start']
            PaginationLength = body['length']
            
            if(PaginationLength != TempLength){ //If pagination length is changed
              dataTablesParameters.start = 0
              body['start'] = 0
              PaginationIndex = 0
              var table = $("#hunt_table").DataTable();
              table.page(0)
            }
            else if(PaginationIndex>TempIndex)   //checking next page index
              {
                uploadData.append('start', NextDataId);
                SelectedNodeID = NextDataId
              }
            else if (PaginationIndex<TempIndex)  //checking Previous page index
              {
                uploadData.append('start', this.PreviousDataIds[PaginationIndex] );
                SelectedNodeID = this.PreviousDataIds[PaginationIndex]
              }
            
            TempIndex = PaginationIndex;
            TempLength = PaginationLength;
            var selectedDate = this.selectedDate['date'];
            if(this.indicatorFile !=undefined && selectedDate!=null ){
                var date = selectedDate.year + '-' + selectedDate.month + '-' + selectedDate.day;
                uploadData.append('indicator_type', this.f.huntType.value[0].id);
                uploadData.append('file', this.indicatorFile[0], this.indicatorFile[0].name);
                uploadData.append('start', dataTablesParameters.start);
                uploadData.append('limit', body['length']);
                uploadData.append('date', date);
                uploadData.append('duration', this.selectedDate['duration']);
            }else{
              this.loading = false;
              $('.table_data').hide();
              return
            }
      let timeoutdone: boolean = false;
      setTimeout(function(){
        timeoutdone = true
      }, environment.nginx_timeout? environment.nginx_timeout: 120000)
      this.http.post<DataTablesResponse>(environment.api_url + "/indicators/upload", uploadData, {
        headers: {
          // 'Content-Type': 'multipart/form-data',
          'x-access-token': localStorage.getItem('token')
        }
      }).subscribe(
        res => {
        this.loading = false
        if(res['status']=='success'){
          this.search_data_output=res.data['results']
          this.search_data_output.forEach((element,index) => {
            let add1 = JSON.stringify(this.search_data_output[index].columns, Object.keys(this.search_data_output[index].columns).sort())

            element["parsedColumns"] = add1;
          });
          this.searchDataOutput=res.data['results']
          $('.table_data').show();
          if(res.data['count'] > 0 && res.data['results'] != undefined)
          {
            this.PreviousDataIds[PaginationIndex]=(this.searchDataOutput[0].id)+1
            NextDataId=(this.searchDataOutput[this.searchDataOutput.length - 1]).id
            $('.dataTables_paginate').show();
            $('.dataTables_info').show();
            $('.dataTables_filter').show()
          }
          else{
            $('.dataTables_paginate').hide();
            $('.dataTables_info').hide();

          }
          callback({
            recordsTotal: res.data['count'],
            recordsFiltered: res.data['count'],
            data: []
          });
        }if(res['status']=='failure'){
          $('.table_data').hide();
          Swal.fire({
            icon: 'warning',
            text:res['message']
            })
        }
      },
      err => {
        $('.dataTables_paginate').hide();
        $('.dataTables_info').hide();
        $("#table_noresults").show()
        $("#DataTables_Table_0_processing").hide()
        $("#DataTables_Table_0_length").hide()
        $("#DataTables_Table_0").hide()
        console.log('error',err)
        if(err.status == 413)
          Swal.fire({
            icon: 'error',
            text: 'Request entity is too large, please upload file less than ' + (this.maxFileSize / 1048576).toFixed(2) + 'MB'
          })
        else if(timeoutdone && (err.status == 502 || err.status == 504)){
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
ngAfterViewInit(): void {
  this.dtTrigger.next();
}
ngOnDestroy(): void {
  this.dtTrigger.unsubscribe();
}
RerenderDatatable(){
  this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
    // Destroy the table first
    dtInstance.destroy();
    // Call the dtTrigger to rerender again
    this.dtTrigger.next();
  });
}
getDate() {
  var today = new Date();
  var date = today.getFullYear() + '-' + (today.getMonth() + 1) + '-' + today.getDate();
  this.maxDate = {year:today.getFullYear(),month:today.getMonth()+ 1,day:today.getDate()+1};
  this.selectedDate['date'] = this.calendar.getToday();
  this.selectedDate['duration']=3;
  this.getHuntList()

}
getconvertedDate() {
  var date =  this.datepickerDate['date'];
  if(date instanceof Date){
    date=this.convertDate(date);
    this.datepickerDate['date']=date
  }
}

convertDate(date) {
  var  mnth = ("0" + (date.getMonth() + 1)).slice(-2),
    day = ("0" + date.getDate()).slice(-2);
  return [date.getFullYear(), mnth, day].join("-");
}
getDuration(duration_period){
  this.selectedDate['duration']=duration_period;
}
action(event): void {
  event.stopPropagation();
}
isDateValid(){
  var date = this.selectedDate['date'];
  if(date == null){
    this.dateIncorrectErrorMsg();
    return;
  }else{
    const tempDateSelected = new Date(this.selectedDate['date'].year, this.selectedDate['date'].month, this.selectedDate['date'].day);
    const tempDateMax = new Date(this.maxDate.year, this.maxDate.month, this.maxDate.day);
    if(tempDateSelected > tempDateMax ||  tempDateSelected.toDateString() == 'Invalid Date' || this.selectedDate['date'] == null){
    this.dateIncorrectErrorMsg();
    return false;
  }
  else{ return true; }
}
}
dateIncorrectErrorMsg(){
  Swal.fire({
    icon: 'warning',
    text: 'Please provide correct date input'
    })
}

}
