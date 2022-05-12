import { AfterViewInit,OnDestroy,Component, OnInit,ViewChild } from '@angular/core';
import { CommonapiService } from '../../dashboard/_services/commonapi.service';
import swal from 'sweetalert';
import { Location } from '@angular/common';
import { saveAs } from 'file-saver';
// declare var $ :any;
import 'datatables.net';
import { DataTableDirective } from 'angular-datatables';
import { Subject } from 'rxjs';
import { HttpClient,HttpEventType,HttpResponse,HttpHeaderResponse } from '@angular/common/http';
import { ToastrService } from 'ngx-toastr';
import { environment } from '../../../environments/environment'
import { AuthorizationService } from '../../dashboard/_services/Authorization.service';
class DataTablesResponse {
  data: any[];
  draw: number;
  recordsFiltered: number;
  recordsTotal: number;
}

class carves_data {
  hostname: string;
  Session: string;
  created_at: string;
  File:any;
  Blocks_Acquired:any
  Status:any;
  Carve_Size:any;
  Delete:string;
}



@Component({
  selector: 'app-carves',
  templateUrl: './carves.component.html',
  styleUrls: ['./carves.component.css']
})
export class CarvesComponent implements AfterViewInit, OnInit {
  @ViewChild(DataTableDirective, {static: false})
  dtElement: DataTableDirective;
  dtTrigger: Subject<any> = new Subject();
  carves_val:any;
  carves_data:any;
  carves_delete:any;
  DownloadCarvesid:any;
  carves_download:any;
  errorMessage:any;
  byte_value: number;
  Progress_value:number = 0;
  dtOptions: DataTables.Settings = {};
  ShowProgress: boolean = false;
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess};
   constructor(
    private commonapi:CommonapiService,
    private _location: Location,
    private http: HttpClient,
    private toastr: ToastrService,
    private authorizationService: AuthorizationService,
  ) { }

  ngOnInit() {
    $('.carves_result').hide()
    // this.getFromAlertData();
    // this.commonapi.carves_api().subscribe(res => {
    //   this.carves_val = res ;
    //   this.carves_data = this.carves_val.data.results;
    //   console.log(this.carves_val);
    // });
    this.dtOptions = {
      pagingType: 'full_numbers',
      pageLength: 10,
      serverSide: true,
      processing: true,
      searching: false,
      ajax: (dataTablesParameters: any,callback) => {
      var body = dataTablesParameters;
      body['limit']=body['length'];
      if(body.search.value!= ""  &&  body.search.value.length>=1)
    {

      body['searchterm']=body.search.value;

    }

      console.log(body,"bodymm",body['searchterm'])


      if(body['searchterm']==undefined){
        body['searchterm']="";
      }
        this.http.post<DataTablesResponse>(environment.api_url+"/carves", body, { headers: { 'Content-Type': 'application/json','x-access-token': localStorage.getItem('token')}}).subscribe(res =>{

          this.carves_val = res ;
            this.carves_data = this.carves_val.data.results;
        if(this.carves_data.length >0 &&  this.carves_data!=undefined)
        {
        this.carves_data = this.carves_val.data['results'];
          // $("#DataTables_Table_0_info").
          $('.dataTables_paginate').show();
          $('.dataTables_info').show();
          $('.dataTables_filter').show()
          $('.carves_result').show()
        }
        else{
          if(body.search.value=="" || body.search.value == undefined)
          {
            this.errorMessage="No Carves created. You may create new Carves";
          }
          else{
            this.errorMessage="No Matching Record Found";
          }

          $('.dataTables_paginate').hide();
          $('.dataTables_info').hide();
          $('.carves_result').hide()
        }
          callback({
            recordsTotal: this.carves_val.data.total_count,
            recordsFiltered: this.carves_val.data.count,
            data: []
          });
        });
      },
      ordering: false,
      columns: [{ data: 'hostname' },{ data: 'session' },{ data: 'carves_size' },{ data: 'files' },{ data: 'blocks_aquire' },{ data: 'status' },{ data: 'created_at' }],
    }


    // $('.popover-dismiss').popover({
    //   trigger: 'focus'
    // })
  }
  ProgressInfos=[];
  FileCount:number=0;
  CurrentFileCount:any;
  ProgressDiv:boolean = false;
  FileId:any;
  InprogessInfo = 0;
  inProgressDownloadList =[];
  downloadCarve(event,carve_hostname,carve_file_name){
    this.ProgressDiv = true;
    var DownloadCarvesid = event.target.id;
    var DownloadCarvesname = event.target.name;
    //Checking file downloading or not
    if(this.ProgressInfos.length > 0){
      var IsFileExist = this.ProgressInfos.find(x=>x.fileName == carve_file_name);
      if (typeof IsFileExist != "undefined") {
           var Progress = IsFileExist.isDownloaded;
           if(Progress == true){ this.toastr.error('File is already downloading');
             return;
           }
           else if(Progress == false){ this.toastr.error('File is already downloaded');
             return;
           }
      }else{
        this.FileCount = this.FileCount +1
      }
    }
    this.ProgressInfos[this.FileCount] = { progress: 0, fileId:DownloadCarvesid, fileName: carve_file_name ,isDownloaded:true};
    this.commonapi.carves_download_api(DownloadCarvesid).subscribe((event)=> {
        //Inprogress File DownloadList
        if(event instanceof HttpHeaderResponse){
          var FileId = DownloadCarvesid;
          this.CurrentFileCount = this.ProgressInfos.findIndex(x=>x.fileId == FileId);
          this.FileId = this.ProgressInfos.find(x=>x.fileId == FileId).fileId;
          var obj =[];
          this.ProgressInfos.forEach(function (Info) {
                 if(Info.isDownloaded == true){
                   obj.push(Info);
                 }
          });
          this.inProgressDownloadList = obj;
        }
        //Completed File DownloadList
        if(event instanceof HttpResponse){
          var FileId = DownloadCarvesid;
          var fileIndex = this.ProgressInfos.findIndex(x=>x.fileId == FileId);
          this.InprogessInfo = this.InprogessInfo+1
          this.ProgressInfos[fileIndex].isDownloaded = false;
        }
     if(event['loaded'] && event['total']){
       var fileIndex = this.ProgressInfos.findIndex(x=>x.fileId == DownloadCarvesid);
       this.ProgressInfos[fileIndex].progress = Math.round(event['loaded']/event['total']*100);
     }

     if(event['body'])
     {
        saveAs(event['body'], carve_file_name+".tar");
        if(this.InprogessInfo == this.ProgressInfos.length){
          swal("File Download Completed", {
            icon: "success",
            buttons: [false],
            timer: 2000
          });
        }
     }
  })

  }

  EventUrlId(event){
    var EventUrl = event['url'].split("//");
    var Url = EventUrl[1].split("/");
    var FileId = Url[6];
    return FileId;
  }

  /*
    This function convert bytes into carvesize format
    */

  getCarvesize(bytes){
   let sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
      if (bytes == 0)
        return '0 Byte';
    this.byte_value = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, this.byte_value)) + ' ' + sizes[this.byte_value];

}
  deleteCarve(event){
        swal({
        icon: 'warning',
        title: "Are you sure?",
        text: "You won't be able to revert this!",
        buttons: ["Cancel", true],
        dangerMode: true,
      }).then((willDelete) => {
        if (willDelete) {
        var idAttr = event.target.id;
        this.commonapi.carves_delete_api(idAttr).subscribe(res => {
          this.carves_delete = res;
          swal("Carve file has been deleted successfully!", {
            icon: "success",
            buttons: [false],
            timer: 2000
          });
          setTimeout(() => {
            this.ngOnInit();
            this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
              // Destroy the table first
              dtInstance.destroy();
              // Call the dtTrigger to rerender again
              this.dtTrigger.next();
            });
          },2100);

        })
      }
})

  }
  ngAfterViewInit(): void {
    this.dtTrigger.next();
  }
  goBack(){
    this._location.back();
  }
  ToggleProgressMenu(){
    if(this.ShowProgress){
      document.getElementById("dropdown-div").classList.remove('show');
      this.ShowProgress = false;
    }else{
      document.getElementById("dropdown-div").classList.add('show');
      this.ShowProgress = true;
    }
}


}
