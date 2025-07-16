// lib/screens/task_search_delegate.dart

import 'package:flutter/material.dart';

/// A SearchDelegate for tasks. Returns the new query as soon as
/// the user submits it (presses the search action on the keyboard).
class TaskSearchDelegate extends SearchDelegate<String?> {
  TaskSearchDelegate() : super(
    // optional: set hint text here
    searchFieldLabel: 'Search tasks…',
  );

  /// This gets called by the framework when the user submits
  /// (presses the search key). We override it to immediately
  /// close the delegate and return the query.
  @override
  void showResults(BuildContext context) {
    close(context, query.trim().isEmpty ? null : query.trim());
  }

  /// We never actually build a “results page” inside the delegate,
  /// because showResults() already closes it.
  @override
  Widget buildResults(BuildContext context) => const SizedBox.shrink();

  /// You can still show suggestions here if you like.
  @override
  Widget buildSuggestions(BuildContext context) {
    return const Center(child: Text('Type to search…'));
  }

  @override
  List<Widget> buildActions(BuildContext context) => [
    IconButton(
      icon: const Icon(Icons.clear),
      onPressed: () {
        if (query.isEmpty) {
          close(context, null);
        } else {
          query = '';
          showSuggestions(context);
        }
      },
    ),
  ];

  @override
  Widget buildLeading(BuildContext context) => IconButton(
    icon: const Icon(Icons.arrow_back),
    onPressed: () => close(context, null),
  );
}