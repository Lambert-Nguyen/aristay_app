// lib/screens/task_search_delegate.dart
import 'package:flutter/material.dart';

/// A SearchDelegate for tasks. Calls [onQuery] when the user submits a search.
typedef OnQueryChanged = void Function(String query);

class TaskSearchDelegate extends SearchDelegate<String?> {
  // drop the callback  from the constructor entirely
  TaskSearchDelegate();

  @override
  Widget buildSuggestions(BuildContext context) {
    // You can show recent searches, etc.
    return const Center(child: Text('Type to search…'));
  }

  @override
  Widget buildResults(BuildContext context) {
    // Just offer a tappable “search for X” and then close with X
    return ListTile(
      title: Text('Search for "$query"'),
      leading: const Icon(Icons.search),
      onTap: () {
        close(context, query);         // ← returns the query to the caller
      },
    );
  }

  @override
  List<Widget> buildActions(BuildContext context) => [
    IconButton(
      icon: const Icon(Icons.clear),
      onPressed: () {
        if (query.isEmpty) {
          close(context, null);       // user wants out
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