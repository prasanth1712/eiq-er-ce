import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { UpdateQueriesInQueriesComponent } from './update-queries-in-queries.component';

describe('UpdateQueriesInQueriesComponent', () => {
  let component: UpdateQueriesInQueriesComponent;
  let fixture: ComponentFixture<UpdateQueriesInQueriesComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ UpdateQueriesInQueriesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UpdateQueriesInQueriesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
