import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { BibliographicStyleSelectorComponent } from './bibliographic-style-selector';

describe('BibliographicStyleSelectorComponent', () => {
  let component: BibliographicStyleSelectorComponent;
  let fixture: ComponentFixture<BibliographicStyleSelectorComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ BibliographicStyleSelectorComponent ],
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BibliographicStyleSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
