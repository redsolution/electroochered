// model function for kindergtn
function KinderGtn(data) {
  var self = this;
  this.id = ko.observable(data.id);
  this.display = ko.observable(true);
  this.errMsg = ko.observable('');
  this.shortName = ko.observable(data.short_name);
  this.ageGroupsIds = ko.observable(data.age_groups);
  this.sadikGroups = ko.observableArray();

  this.addSadikGroup = function(data, ageGroups) {
    var sadikGroup = new SadikGroup(data, ageGroups);
    this.sadikGroups.push(sadikGroup);
    return sadikGroup;
  };

}

function AgeGroup(data) {
  this.id = ko.observable(data.id);
  this.name = ko.observable(data.name);
  this.shortName = ko.observable(data.short_name);
  this.minBirthDate = ko.observable(data.min_birth_date);
  this.maxBirthDate = ko.observable(data.max_birth_date);
}

function SadikGroup(data, ageGroups) {
  self = this;
  this.id = ko.observable(data.id || '');
  this.capacity = ko.observable(data.capacity || 0);
  this.freePlaces = ko.observable(data.free_places || 0);
  this.ageGroup = ko.observable(data.age_group);
  this.renderName = ko.observable();

  this.ageGroups = ageGroups;

  this.name = ko.pureComputed(function() {
    var ageGroupId = self.ageGroup();
    var ageGroup = ko.utils.arrayFirst(self.ageGroups(), function(item) {
      return item.id() === ageGroupId;
    });
    return ageGroup.name();
  }, this);
}



function KgListViewModel() {
  var self = this;
  this.KinderGtnList = ko.observableArray();
  this.filterText = ko.observable('');

  this.ageGroups = ko.observableArray();

  // selecting kindergartens to show on the page, filtering them
  this.kindergtnsToShow = ko.pureComputed(function() {
    var text = this.filterText().toLowerCase();
    if (text) {
      return ko.utils.arrayFilter(this.KinderGtnList(), function(kg) {
        return kg.shortName().toLowerCase().indexOf(text) > -1;
      });
    }
    return this.KinderGtnList();
  }, this);

  this.renderSadikGroups = function(kg) {
    if (!kg.sadikGroups().length) {
      self.getSadikGroups(kg);
      var filteredAgeGroups = ko.mapping.toJS(ko.utils.arrayFilter(self.ageGroups(), function(item) {
        return kg.ageGroupsIds().indexOf(item.id()) > -1;
      }));
      filteredAgeGroups.forEach(function(data) {
        kg.addAgeGroup(data);
      });
    }
  };

  this.getSadikGroups = function(kg, event) {
    // block default slidup untill we get all groups
    event.stopPropagation();
    var el = $(event.target).parents('.accordion-group').find('.accordion-body');
    if (kg.sadikGroups().length || !kg.display()) {
      el.collapse('toggle');
      return;
    }

    $.getJSON('/api2/sadik/' + kg.id() + '/groups/', function(data) {
      $.each(kg.ageGroupsIds(), function(key, val) {
        // ищем подходящую группу среди полученных активных групп в садике
        sadikGroup = data.filter(function(item) {
          return item.age_group == val;
        });
        // если такая группа есть и она одна - используем её данные
        if (sadikGroup.length == 1) {
          kg.addSadikGroup(sadikGroup[0], self.ageGroups);
          // если таких групп несколько - ошибка, запрещаем работу с ДОУ
        } else if (sadikGroup.length > 1) {
          kg.display(false);
          kg.errMsg('Данный ДОУ содержит более одной активной группы для определенного возраста. Сообщите о проблеме в техническую поддержку.')
            // если такой группы нет - создаем новую
        } else {
          kg.addSadikGroup({'age_group': val}, self.ageGroups);
        }
      });
      el.collapse('show');
    }).error(function(e) {
      console.log('error while downloading sadikgroups list');
    });
  };

  // downloading json of kindergartens objects
  $.getJSON('/api2/sadik/simple_info/', function(data) {
    $.each(data, function(key, val) {
      self.KinderGtnList.push(new KinderGtn(val));
    });
  }).error(function(e) {
    console.log('error while downloading kindergtns list');
  });

  // downloading json of agegroups objects
  $.getJSON('/api2/age_groups/', function(data) {
    $.each(data, function(key, val) {
      self.ageGroups.push(new AgeGroup(val));
    });
  }).error(function(e) {
    console.log('error while downloading agegroups list');
  });
}

ko.applyBindings(new KgListViewModel());

ko.bindingHandlers.highlightedText = {
  update: function(element, valueAccessor) {
    var options = valueAccessor();
    var value = ko.utils.unwrapObservable(options.text);
    var search = ko.utils.unwrapObservable(options.highlight);
    // remove previous highlight, if no filter value present
    if (search.length === 0) {
      element.innerHTML = value;
      return;
    }
    // could do this or something similar to escape HTML before replacement,
    // if there is a risk of HTML injection in this value
    if (options.sanitize) {
      value = $('<div/>').text(value).html();
    }
    var re = new RegExp(search, 'ig');
    // if found matches - highlighting them
    var match = value.match(re);
    if (match) {
      var replacement = '<span class="highlight">' + match[0] + '</span>';
      element.innerHTML = value.replace(re, replacement);
    }
  }
};
