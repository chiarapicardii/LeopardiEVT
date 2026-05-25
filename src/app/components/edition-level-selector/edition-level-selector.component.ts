import { Component, Input, OnDestroy, Output } from '@angular/core';
import { BehaviorSubject, combineLatest, of, Subscription } from 'rxjs';
import { distinctUntilChanged, filter, map } from 'rxjs/operators';
import { AppConfig, EditionLevel, EditionLevelType } from '../../app.config';
import { EvtIconInfo } from '../../ui-components/icon/icon.component';
import { EVTStatusService } from 'src/app/services/evt-status.service';

@Component({
  selector: 'evt-edition-level-selector',
  templateUrl: './edition-level-selector.component.html',
  styleUrls: ['./edition-level-selector.component.scss'],
})
export class EditionLevelSelectorComponent implements OnDestroy {
  private subscriptions: Subscription;
  public editionLevels = (AppConfig.evtSettings.edition.availableEditionLevels || []).filter((el) => el.enable);
  public selectableEditionLevels: EditionLevel[] = this.editionLevels.filter((el) => !el.hidden);

  private _edLevelID: EditionLevelType;
  @Input() set editionLevelID(p: EditionLevelType) {
    this.subscriptions = this.evtStatusService.currentViewMode$.pipe().subscribe((view) => {
      if (view !== undefined && (view.id === 'documentalMixed')) {
        // documental mixed only allows changesView
        this._edLevelID = 'changesView';
        this.selectedEditionLevel$.next('changesView');
      } else {
        if (this.selectableEditionLevels.some((ed) => ed.id === p)) {
          this._edLevelID = p;
          this.selectedEditionLevel$.next(this._edLevelID);
        } else {
          // if the provided edition id doesn't exist (or is hidden/disabled)
          // fallback to a default edition
          this._edLevelID = this.selectableEditionLevels[0].id;
          this.selectedEditionLevel$.next(this._edLevelID);
        }
      }
    });
  }
  get editionLevelID() { return this._edLevelID; }

  selectedEditionLevel$ = new BehaviorSubject<EditionLevelType>(undefined);

  @Output() selectionChange = combineLatest([
    of(this.editionLevels),
    this.selectedEditionLevel$.pipe(distinctUntilChanged()),
  ]).pipe(
    filter(([edLevels, edLevelID]) => !!edLevelID && !!edLevels && edLevels.length > 0),
    map(([edLevels, edLevelID]) => !!edLevelID ? edLevels.find((p) => p.id === edLevelID) || edLevels[0] : edLevels[0]),
    filter((e) => !!e),
  );

  icon: EvtIconInfo = {
    icon: 'layer-group', // TODO: Choose better icon
    additionalClasses: 'me-2',
  };

  stopPropagation(event: MouseEvent) {
    event.stopPropagation();
  }

  ngOnDestroy() {
    this.subscriptions.unsubscribe();
  }

  constructor(
    private evtStatusService: EVTStatusService,
  ){}

}
