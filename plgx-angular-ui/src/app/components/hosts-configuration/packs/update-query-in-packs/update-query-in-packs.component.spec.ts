import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { UpdateQueryInPacksComponent } from './update-query-in-packs.component';

describe('UpdateQueryInPacksComponent', () => {
  let component: UpdateQueryInPacksComponent;
  let fixture: ComponentFixture<UpdateQueryInPacksComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ UpdateQueryInPacksComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UpdateQueryInPacksComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
