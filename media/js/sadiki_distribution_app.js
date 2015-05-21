// model function for kindergtn
function KinderGtn(data) {
  this.id = ko.observable(data.id);
  this.shortName = ko.observable(data.short_name);
  this.ageGroupsIds = ko.observable(data.age_groups);
  this.ageGroups = ko.observableArray();

  this.addAgeGroup = function(data) {
    this.ageGroups.push(new AgeGroup(data));
  };
}

function AgeGroup(data) {
  this.id = ko.observable(data.id);
  this.name = ko.observable(data.name);
  this.shortName = ko.observable(data.short_name);
  this.minBirthDate = ko.observable(data.min_birth_date);
  this.maxBirthDate = ko.observable(data.max_birth_date);
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

  this.getAgeGroups = function(kg) {
    if (kg.ageGroups().length != kg.ageGroupsIds().length) {
      kg.ageGroups.removeAll();
      var filteredAgeGroups = ko.mapping.toJS(ko.utils.arrayFilter(self.ageGroups(), function(item) {
        return kg.ageGroupsIds().indexOf(item.id()) > -1;
      }));
      filteredAgeGroups.forEach(function(data) {
        kg.addAgeGroup(data);
      });
    }
  };

  // downloading json of kindergartens objects
  $.getJSON('/api2/get_simple_kg_info/', function(data) {
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
